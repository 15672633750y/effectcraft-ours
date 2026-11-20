#!/usr/bin/env python3
"""账号与资料 · 第一包：HTTP 客户端（不含任何 UI）。

后端 `https://shimoveaex-api.3264003615.workers.dev`：
- `POST /auth/login` {username,password} → {ok, token, user}
- `GET  /me`  Authorization: Bearer <token> → {ok, user}（user.prefs 里放 profile）
- `PUT  /me`  {display_name, prefs_json} → {ok, user}（后端 prefs 上限 8 KB，所以头像不进 prefs）

选 ureq 3.5.0 的原因：它已经在 Cargo.lock 里（rustls 0.23 + ring，没有 aws-lc-rs），
上游构建一直在交叉编译它，所以 Android 上不需要新增任何 crate、也不会引入 C 构建。

本包只做三件事：加依赖、加 `cloud` 模块、把模块注册进 lib.rs。UI 下一包再接。
请求一律在后台线程跑，UI 只搬 `poll()` 的结果；失败只返回字符串，不 panic、不打印 token。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CLOUD_HTTP_V1"

CARGO_ANCHOR = "sys-locale = { workspace = true }\n"
CARGO_INSERT = (
    "sys-locale = { workspace = true }\n"
    "# EFFECTCRAFT_OURS_CLOUD_HTTP_V1 — 账号/资料用的 HTTP 客户端。ureq 3.5.0 本来就在\n"
    "# Cargo.lock 里（craft-update 也在用，rustls 0.23 + ring），这里只是给本 crate 加一条依赖边。\n"
    "ureq = \"=3.5.0\"\n"
)

LIB_ANCHOR = "pub mod color_picker;\n"
LIB_INSERT = "pub mod color_picker;\npub mod cloud;\n"

CLOUD_RS = r'''//! EFFECTCRAFT_OURS_CLOUD_HTTP_V1 — 账号与资料（只有 HTTP 与本地 token，还没有 UI）。
//!
//! 后端规则（见 `云账号/worker.js`）：
//! - `POST /auth/login` {username, password} → {ok, token, user}
//! - `GET /me`  Bearer <token> → {ok, user}；`user.prefs.profile` 放性别/生日/签名
//! - `PUT /me`  {display_name, prefs_json} → {ok, user}；`prefs_json` 上限 8 KB（头像不进这里）
//!
//! 请求全部在后台线程跑，UI 只搬 [`poll`] 拿到的结果。任何失败都只是错误文本：
//! 不 panic、不 blocking UI、不把 token 写进日志。

use std::sync::{Mutex, OnceLock};

/// 后端地址（Cloudflare Workers）。
pub const BASE_URL: &str = "https://shimoveaex-d1ggbg2thbf67172a-1537568735.ap-shanghai.app.tcloudbase.com/api";

/// 云端工程的一条记录。
#[derive(Clone, Debug, Default)]
pub struct RemoteProject {
    pub id: String,
    pub name: String,
    pub size_bytes: u64,
    pub updated_at: u64,
}

impl RemoteProject {
    fn from_value(value: &serde_json::Value) -> Self {
        Self {
            id: value["id"].as_str().unwrap_or_default().to_string(),
            name: value["name"].as_str().unwrap_or("未命名").to_string(),
            size_bytes: value["size_bytes"].as_u64().unwrap_or(0),
            updated_at: value["updated_at"].as_u64().unwrap_or(0),
        }
    }
}

/// 资料卡里的字段。昵称走后端原生 `display_name`，其余放进 `prefs.profile`。
#[derive(Clone, Default, Debug, PartialEq, Eq)]
pub struct Profile {
    pub nickname: String,
    pub gender: String,
    pub birthday: String,
    pub signature: String,
}

impl Profile {
    /// 从返回的 `user` 对象里读（缺字段一律当空串，坏数据不会让界面崩）。
    pub fn from_user(user: &serde_json::Value) -> Self {
        let prefs = &user["prefs"]["profile"];
        let text = |v: &serde_json::Value, k: &str| v[k].as_str().unwrap_or_default().to_string();
        Self {
            nickname: user["display_name"].as_str().unwrap_or_default().to_string(),
            gender: text(prefs, "gender"),
            birthday: text(prefs, "birthday"),
            signature: text(prefs, "signature"),
        }
    }

    /// 写回后端时只要 profile 这一份。
    pub fn to_prefs(&self) -> serde_json::Value {
        serde_json::json!({
            "profile": {
                "gender": self.gender,
                "birthday": self.birthday,
                "signature": self.signature,
            }
        })
    }
}

/// 后台线程推给 UI 的结果。
#[derive(Clone, Debug)]
pub enum Event {
    LoggedIn { token: String, username: String, profile: Profile },
    LoginFailed(String),
    Profile(Profile),
    SaveOk,
    SaveFailed(String),
    /// 读资料/网络出错（不是保存失败）。
    Failed(String),
    /// token 过期：已经清掉本地 token，界面回到未登录。
    SessionExpired,
    /// 账号被封禁：token 已清掉，带上后端给的原因原文。
    Banned(String),
    /// 云端工程列表（名称/大小/更新时间）。
    Projects(Vec<RemoteProject>),
    /// 正在上传（true）/ 上传结束（false）。
    Uploading(bool),
    Uploaded(String),
    /// 下载完成，路径可直接交给 `file.open`。
    Downloaded(String),
    Deleted(String),
    /// 云端操作的失败（配额/未登录/网络各有中文提示）。
    CloudFailed(String),
}

fn events() -> &'static Mutex<Vec<Event>> {
    static QUEUE: OnceLock<Mutex<Vec<Event>>> = OnceLock::new();
    QUEUE.get_or_init(|| Mutex::new(Vec::new()))
}

fn push(event: Event) {
    if let Ok(mut queue) = events().lock() {
        queue.push(event);
    }
}

/// UI 每帧调用一次：拿走所有已完成的结果（没有就返回空）。
pub fn poll() -> Vec<Event> {
    events().lock().map(|mut queue| std::mem::take(&mut *queue)).unwrap_or_default()
}

/// 后台跑一个任务；web 构建没有线程，直接丢弃（那边也不做账号）。
fn spawn(job: impl FnOnce() + Send + 'static) {
    #[cfg(not(target_arch = "wasm32"))]
    std::thread::spawn(job);
    #[cfg(target_arch = "wasm32")]
    {
        let _ = job;
    }
}

// ---------------------------------------------------------------- token 持久化

fn config_dir() -> std::path::PathBuf {
    // builder 给 app 设了 XDG_CONFIG_HOME（应用私有外部目录），优先用它。
    if let Ok(dir) = std::env::var("XDG_CONFIG_HOME") {
        if !dir.is_empty() {
            return std::path::PathBuf::from(dir);
        }
    }
    std::path::PathBuf::from("/storage/emulated/0/DCIM/EffectCraft")
}

fn account_path() -> std::path::PathBuf {
    config_dir().join("account.json")
}

/// 读本地 token；没有、读不到、JSON 坏了都当未登录。
pub fn load_token() -> Option<String> {
    load_account().map(|(token, _)| token)
}

/// 本地存的 (token, username)：头像按 username 命名，所以两个都要。
pub fn load_account() -> Option<(String, String)> {
    let text = std::fs::read_to_string(account_path()).ok()?;
    let value: serde_json::Value = serde_json::from_str(&text).ok()?;
    let token = value["token"].as_str().filter(|t| !t.is_empty())?.to_string();
    let username = value["username"].as_str().unwrap_or_default().to_string();
    Some((token, username))
}

pub fn save_token(token: &str, username: &str) {
    let _ = std::fs::create_dir_all(config_dir());
    let body = serde_json::json!({ "token": token, "username": username }).to_string();
    // TODO(keystore): 换 Android Keystore；先落在应用私有外部目录，别的应用读不到。
    let _ = std::fs::write(account_path(), body);
}

/// 旧版单文件头像（没有登录账号时用它当兜底）。343 曾把它加在这里，
/// 后来 343 并入 341 变成了空操作，这个函数就必须由 340 自己提供。
pub fn avatar_path() -> std::path::PathBuf {
    config_dir().join("avatar.png")
}

/// 头像目录：`<config>/avatar/`，每个账号一张 `<username>.png`（256×256 正方形）。
pub fn avatar_dir() -> std::path::PathBuf {
    config_dir().join("avatar")
}

/// 某个账号的头像文件。
pub fn avatar_file(username: &str) -> std::path::PathBuf {
    avatar_dir().join(format!("{}.png", sanitize(username)))
}

/// 用户名只允许字母数字下划线，落到文件名前再洗一遍，避免路径穿越。
fn sanitize(name: &str) -> String {
    name.chars().map(|c| if c.is_ascii_alphanumeric() || c == '_' { c } else { '_' }).collect()
}

pub fn clear_token() {
    let _ = std::fs::remove_file(account_path());
}

// ---------------------------------------------------------------- HTTP

/// 发一次请求，返回 (状态码, 响应体)。非 2xx 在 ureq 里是 `Error::StatusCode`，
/// 这里照样换算成状态码，好让调用方区分 401（密码错）和网络错误。
///
/// 注意：`ureq::get()` 是 `RequestBuilder<WithoutBody>`，`post/put` 是 `<WithBody>`，
/// 两者类型不同，所以不能放进同一个 match 里返回。
/// 所有请求共用一个 Agent：连接池可以复用，更重要的是**有超时**——
/// 没有超时的话服务器不回包，后台线程会永远挂着，界面上就是「点了没反应」。
#[cfg(not(target_arch = "wasm32"))]
fn agent() -> ureq::Agent {
    static AGENT: OnceLock<ureq::Agent> = OnceLock::new();
    AGENT
        .get_or_init(|| {
            ureq::Agent::config_builder()
                .timeout_global(Some(std::time::Duration::from_secs(10)))
                // 关键：非 2xx 也当正常响应返回。ureq 默认把 4xx/5xx 变成
                // Error::StatusCode，那个错误里**没有响应体**，于是 429 的
                // {code:"LOGIN_RATE_LIMITED", message} 根本读不到，界面上只能
                // 显示一句通用兜底。
                .http_status_as_error(false)
                .build()
                .into()
        })
        .clone()
}

#[cfg(not(target_arch = "wasm32"))]
fn request(method: &str, path: &str, token: Option<&str>, body: Option<&str>) -> Result<(u16, String), String> {
    let url = format!("{BASE_URL}{path}");
    let bearer = token.map(|t| format!("Bearer {t}"));
    let agent = agent();
    let result = if method == "GET" || body.is_none() {
        let req = agent.get(&url);
        let req = match &bearer {
            Some(b) => req.header("Authorization", b.as_str()),
            None => req,
        };
        req.header("Accept", "application/json").call()
    } else {
        let req = if method == "PUT" { agent.put(&url) } else { agent.post(&url) };
        let req = match &bearer {
            Some(b) => req.header("Authorization", b.as_str()),
            None => req,
        };
        req.header("Accept", "application/json")
            .header("Content-Type", "application/json")
            .send(body.unwrap_or(""))
    };
    match result {
        Ok(mut resp) => {
            let code = resp.status().as_u16();
            let text = resp.body_mut().read_to_string().unwrap_or_default();
            Ok((code, text))
        }
        Err(ureq::Error::StatusCode(code)) => Ok((code, String::new())),
        Err(err) => Err(describe(&err)),
    }
}

/// `io: unexpected end of file` 这种错误信息没法定位，按 ureq 的错误类型翻成人话，
/// 方便用户直接告诉我们卡在 DNS、连接、TLS 还是收发上。
fn describe(err: &ureq::Error) -> String {
    match err {
        ureq::Error::StatusCode(code) => format!("服务端返回 HTTP {code}"),
        ureq::Error::BadUri(_) => "请求地址不合法".to_string(),
        ureq::Error::Protocol(_) => "服务端响应格式异常（可能被网络中间设备改写）".to_string(),
        ureq::Error::Io(io) => match io.kind() {
            std::io::ErrorKind::UnexpectedEof => {
                "连接被中途关闭（TLS 握手或响应被中断，常见于网络干扰/代理）".to_string()
            }
            std::io::ErrorKind::TimedOut | std::io::ErrorKind::WouldBlock => "连接超时".to_string(),
            std::io::ErrorKind::ConnectionRefused => "连接被拒绝".to_string(),
            std::io::ErrorKind::ConnectionReset => "连接被重置（网络干扰）".to_string(),
            std::io::ErrorKind::AddrNotAvailable | std::io::ErrorKind::NotFound => "域名解析失败".to_string(),
            _ => format!("网络错误: {io}"),
        },
        other => format!("请求失败: {other}"),
    }
}

#[cfg(target_arch = "wasm32")]
fn request(_method: &str, _path: &str, _token: Option<&str>, _body: Option<&str>) -> Result<(u16, String), String> {
    Err("web build has no network".to_string())
}

/// 上传工程包：裸二进制（`application/octet-stream`），不 base64、不 multipart。
#[cfg(not(target_arch = "wasm32"))]
fn request_bytes(method: &str, path: &str, token: Option<&str>, body: &[u8]) -> Result<(u16, Vec<u8>), String> {
    let url = format!("{BASE_URL}{path}");
    let agent = agent();
    let req = if method == "PUT" { agent.put(&url) } else { agent.post(&url) };
    let req = match token {
        Some(t) => req.header("Authorization", format!("Bearer {t}")),
        None => req,
    };
    match req
        .header("Accept", "application/json")
        .header("Content-Type", "application/octet-stream")
        .send(body)
    {
        Ok(mut resp) => {
            let code = resp.status().as_u16();
            let mut buf = Vec::new();
            resp.body_mut().read_to_vec().map(|v| buf = v).ok();
            Ok((code, buf))
        }
        Err(ureq::Error::StatusCode(code)) => Ok((code, Vec::new())),
        Err(err) => Err(describe(&err)),
    }
}

#[cfg(target_arch = "wasm32")]
fn request_bytes(_method: &str, _path: &str, _token: Option<&str>, _body: &[u8]) -> Result<(u16, Vec<u8>), String> {
    Err("web build has no network".to_string())
}

/// 下载工程包：拿原始字节。
#[cfg(not(target_arch = "wasm32"))]
fn download_bytes(path: &str, token: &str) -> Result<Vec<u8>, String> {
    let url = format!("{BASE_URL}{path}");
    match agent().get(&url).header("Authorization", format!("Bearer {token}")).call() {
        Ok(resp) => {
            let mut resp = resp;
            resp.body_mut().read_to_vec().map_err(|e| format!("读取失败: {e}"))
        }
        Err(ureq::Error::StatusCode(code)) => Err(cloud_hint(code, &serde_json::Value::Null)),
        Err(err) => Err(describe(&err)),
    }
}

#[cfg(target_arch = "wasm32")]
fn download_bytes(_path: &str, _token: &str) -> Result<Vec<u8>, String> {
    Err("web build has no network".to_string())
}

fn json_or_null(text: &str) -> serde_json::Value {
    serde_json::from_str(text).unwrap_or(serde_json::Value::Null)
}

/// 解算数题：后端出的是 "3 + 5" / "9 - 2" 这种两个 1~9 的操作数（文档 3.0 节给了同样的做法）。
/// 题目只含 ASCII，所以按字节切分是安全的。
fn solve(question: &str) -> Option<i32> {
    let compact: String = question.chars().filter(|c| !c.is_whitespace()).collect();
    let pos = compact.find(|c| c == '+' || c == '-')?;
    let (lhs, rest) = compact.split_at(pos);
    let op = rest.chars().next()?;
    let a: i32 = lhs.parse().ok()?;
    let b: i32 = rest.get(1..)?.parse().ok()?;
    Some(if op == '+' { a + b } else { a - b })
}

/// 取一道人机校验题并算好答案。取不到就返回 None（提交时就不带这两个字段，
/// 老后端不需要它们，新后端会回 CAPTCHA_REQUIRED，上层会换题重试）。
fn captcha_pair() -> Option<(String, i32)> {
    let (code, text) = request("GET", "/auth/captcha", None, None).ok()?;
    if !(200..300).contains(&code) {
        return None;
    }
    let value = json_or_null(&text);
    let id = value["id"].as_str()?.to_string();
    let answer = solve(value["question"].as_str()?)?;
    Some((id, answer))
}

/// 提交注册/登录：每次现取一道题；后端说 CAPTCHA_INVALID / CAPTCHA_REQUIRED 就换一道再来。
/// 最多两次，避免在后端异常时死循环。
fn post_auth(path: &str, username: &str, password: &str) -> Result<(u16, String), String> {
    let mut last = String::new();
    for _ in 0..2 {
        let mut body = serde_json::json!({ "username": username, "password": password });
        if let Some((id, answer)) = captcha_pair() {
            body["captcha_id"] = serde_json::json!(id);
            body["captcha_answer"] = serde_json::json!(answer);
        }
        let text = body.to_string();
        let (code, response) = request("POST", path, None, Some(&text))?;
        let value = json_or_null(&response);
        let api = value["code"].as_str().unwrap_or_default();
        if api == "CAPTCHA_INVALID" || api == "CAPTCHA_REQUIRED" {
            last = "人机校验没通过，正在重试…".to_string();
            continue;
        }
        // 账号被停用：这类响应不能重试，也不能当成「密码错」。
        if api == "ACCOUNT_BANNED" {
            clear_token();
            return Err(banned_text(&value));
        }
        return Ok((code, response));
    }
    Err(if last.is_empty() { "人机校验连续失败，请稍后再试".to_string() } else { last })
}

/// 封禁提示：后端给的 reason 原文优先，没有就退回 message，最后才用兜底文案。
fn banned_text(value: &serde_json::Value) -> String {
    let reason = value["reason"]
        .as_str()
        .or_else(|| value["data"]["reason"].as_str())
        .or_else(|| value["error"]["reason"].as_str())
        .or_else(|| value["message"].as_str())
        .or_else(|| value["error"]["message"].as_str())
        .unwrap_or("该账号已被停用");
    if reason.contains("停用") || reason.contains("封") {
        reason.to_string()
    } else {
        format!("该账号已被停用：{reason}")
    }
}

/// 登录失败时给用户的一句话（不泄露账号是否存在）。
fn login_hint(code: u16, value: &serde_json::Value) -> String {
    // 后端错误形状是 {"ok":false,"code":"...","message":"中文提示"}（文档第 0 节）。
    let api = value["code"]
        .as_str()
        .or_else(|| value["error"]["code"].as_str())
        .unwrap_or_default();
    let server_message = value["message"]
        .as_str()
        .or_else(|| value["error"]["message"].as_str())
        .unwrap_or_default();
    // 账号不存在和密码错误后端给的是同一句话，直接用它，不要自己加工。
    if api == "CREDENTIALS_INVALID" || code == 401 {
        return "用户名或密码错误".to_string();
    }
    if api == "CAPTCHA_INVALID" || api == "CAPTCHA_REQUIRED" {
        return "人机校验没通过，请再试一次".to_string();
    }
    // 限流必须排在「透传后端 message」**之前**：后端对 429 给的原文是
    // 「登录尝试过于频繁，请稍后再试」，直接透传就永远看不到具体要等几分钟。
    if api == "LOGIN_RATE_LIMITED" || api == "REGISTER_RATE_LIMITED" || code == 429 {
        let seconds = value["retry_after"]
            .as_u64()
            .or_else(|| value["retryAfter"].as_u64())
            .or_else(|| value["data"]["retry_after"].as_u64())
            .unwrap_or(60);
        let minutes = seconds.div_ceil(60).max(1);
        let what = if api == "REGISTER_RATE_LIMITED" { "注册" } else { "登录" };
        return format!("{what}尝试过于频繁，请 {minutes} 分钟后重试");
    }
    if !server_message.is_empty() {
        return server_message.to_string();
    }
    match api {
        "USERNAME_TAKEN" => "用户名已被占用",
        "USERNAME_INVALID" => "用户名只能用 3~20 位字母、数字、下划线",
        "WEAK_PASSWORD" => "密码至少 8 位，别用常见密码",
        "PREFS_TOO_LARGE" => "资料内容太长",
        _ if code == 0 => "网络不可用，请检查网络后重试",
        _ => "请求失败，请稍后再试",
    }
    .to_string()
}

// ---------------------------------------------------------------- 对外动作

/// 登录：成功就记住 token 并推 [`Event::LoggedIn`]。
pub fn login(username: String, password: String) {
    spawn(move || {
        match post_auth("/auth/login", &username, &password) {
            Ok((code, text)) => {
                let value = json_or_null(&text);
                let token = value["token"].as_str().unwrap_or_default().to_string();
                // 实测：登录回 200，注册回 **201** —— 只认 200 的话注册会永远提示失败。
                if (200..300).contains(&code) && !token.is_empty() {
                    let username = value["user"]["username"].as_str().unwrap_or_default().to_string();
                    save_token(&token, &username);
                    // 能登录成功说明不再被封：把上次的原因清掉。
                    clear_banned();
                    push(Event::LoggedIn { token, username, profile: Profile::from_user(&value["user"]) });
                } else {
                    push(Event::LoginFailed(login_hint(code, &value)));
                }
            }
            Err(err) => {
                if err.contains("已被停用") {
                    push(Event::Banned(err));
                } else {
                    push(Event::LoginFailed(err));
                }
            }
        }
    });
}

/// 注册：成功同样直接登录。
pub fn register(username: String, password: String) {
    spawn(move || {
        match post_auth("/auth/register", &username, &password) {
            Ok((code, text)) => {
                let value = json_or_null(&text);
                let token = value["token"].as_str().unwrap_or_default().to_string();
                // 实测：登录回 200，注册回 **201** —— 只认 200 的话注册会永远提示失败。
                if (200..300).contains(&code) && !token.is_empty() {
                    let username = value["user"]["username"].as_str().unwrap_or_default().to_string();
                    save_token(&token, &username);
                    // 能登录成功说明不再被封：把上次的原因清掉。
                    clear_banned();
                    push(Event::LoggedIn { token, username, profile: Profile::from_user(&value["user"]) });
                } else {
                    push(Event::LoginFailed(login_hint(code, &value)));
                }
            }
            Err(err) => {
                if err.contains("已被停用") {
                    push(Event::Banned(err));
                } else {
                    push(Event::LoginFailed(err));
                }
            }
        }
    });
}

/// 用已存的 token 拉一次资料（启动时用；token 失效会静默回到未登录）。
pub fn fetch_me(token: String) {
    spawn(move || match request("GET", "/me", Some(&token), None) {
        Ok((code, text)) if (200..300).contains(&code) => {
            let value = json_or_null(&text);
            push(Event::Profile(Profile::from_user(&value["user"])));
        }
        Ok((401, _)) => {
            clear_token();
            push(Event::SessionExpired);
        }
        Ok((_, text)) => push(Event::Failed(text)),
        Err(err) => push(Event::Failed(err)),
    });
}

/// 保存资料卡：昵称写 `display_name`，其余写 `prefs_json.profile`。
pub fn save_profile(token: String, profile: Profile) {
    spawn(move || {
        let body = serde_json::json!({
            "display_name": profile.nickname.clone(),
            // 用户明确要求字段放 prefs_json.profile（文档里写的是 prefs，后端两个都收）。
            "prefs_json": profile.to_prefs(),
        })
        .to_string();
        match request("PUT", "/me", Some(&token), Some(&body)) {
            Ok((code, _)) if (200..300).contains(&code) => push(Event::SaveOk),
            Ok((401, _)) => {
                clear_token();
                push(Event::SessionExpired);
            }
            Ok((_, text)) => push(Event::SaveFailed(text)),
            Err(err) => push(Event::SaveFailed(err)),
        }
    });
}

/// 退出登录：只清本地 token，本地工程一点不动。
pub fn logout() {
    clear_token();
}

// ---------------------------------------------------------------- 云端工程

/// 云端操作的失败提示：配额/未登录/存储关闭各有自己的话。
fn cloud_hint(code: u16, value: &serde_json::Value) -> String {
    let api = value["code"]
        .as_str()
        .or_else(|| value["error"]["code"].as_str())
        .unwrap_or_default();
    let server = value["message"]
        .as_str()
        .or_else(|| value["error"]["message"].as_str())
        .unwrap_or_default();
    match api {
        "UNAUTHENTICATED" | "TOKEN_EXPIRED" | "TOKEN_INVALID" | "SESSION_REVOKED" => {
            "登录已失效，请重新登录".to_string()
        }
        "QUOTA_EXCEEDED" | "STORAGE_FULL" => "云空间不足，请先删掉一些云端工程".to_string(),
        "STORAGE_DISABLED" => "云端存储暂未开放".to_string(),
        "PROJECT_NOT_FOUND" => "这个云端工程已经不存在了".to_string(),
        "NAME_REQUIRED" | "PROJECT_NAME_INVALID" => "工程名不能为空".to_string(),
        _ if code == 401 => "登录已失效，请重新登录".to_string(),
        _ if !server.is_empty() => server.to_string(),
        _ if code == 0 => "网络不可用，请检查网络后重试".to_string(),
        _ => format!("云端请求失败（HTTP {code}）"),
    }
}

/// `GET /projects`：拉云端工程列表。
pub fn list_projects(token: String) {
    spawn(move || match request("GET", "/projects", Some(&token), None) {
        Ok((code, text)) => {
            let value = json_or_null(&text);
            if code == 401 {
                clear_token();
                push(Event::SessionExpired);
                return;
            }
            if !(200..300).contains(&code) {
                push(Event::CloudFailed(cloud_hint(code, &value)));
                return;
            }
            let list = value["projects"]
                .as_array()
                .map(|items| items.iter().map(RemoteProject::from_value).collect())
                .unwrap_or_default();
            push(Event::Projects(list));
        }
        Err(err) => push(Event::CloudFailed(err)),
    });
}

/// 上传：`POST /projects` 拿 id，再 `PUT /projects/:id/content` 发原始字节。
pub fn upload_project(token: String, name: String, bytes: Vec<u8>) {
    spawn(move || {
        push(Event::Uploading(true));
        let body = serde_json::json!({ "name": name }).to_string();
        let created = match request("POST", "/projects", Some(&token), Some(&body)) {
            Ok((code, text)) => (code, json_or_null(&text)),
            Err(err) => {
                push(Event::Uploading(false));
                push(Event::CloudFailed(err));
                return;
            }
        };
        let (code, value) = created;
        if !(200..300).contains(&code) {
            push(Event::Uploading(false));
            push(Event::CloudFailed(cloud_hint(code, &value)));
            return;
        }
        let Some(id) = value["project"]["id"].as_str().filter(|s| !s.is_empty()) else {
            push(Event::Uploading(false));
            push(Event::CloudFailed("后端没有返回工程 id".to_string()));
            return;
        };
        let path = format!("/projects/{id}/content");
        match request_bytes("PUT", &path, Some(&token), &bytes) {
            Ok((code, body)) => {
                push(Event::Uploading(false));
                if (200..300).contains(&code) {
                    push(Event::Uploaded(name));
                } else {
                    push(Event::CloudFailed(cloud_hint(code, &json_or_null(&String::from_utf8_lossy(&body)))));
                }
            }
            Err(err) => {
                push(Event::Uploading(false));
                push(Event::CloudFailed(err));
            }
        }
    });
}

/// 下载到 `<config>/cloud/<name>.ecproj`，路径交给 `file.open`。
pub fn download_project(token: String, id: String, name: String) {
    spawn(move || {
        match download_bytes(&format!("/projects/{id}/content"), &token) {
            Ok(bytes) if !bytes.is_empty() => {
                let dir = cloud_dir();
                if std::fs::create_dir_all(&dir).is_err() {
                    push(Event::CloudFailed("写不了下载目录".to_string()));
                    return;
                }
                let safe: String = name
                    .chars()
                    .map(|c| if c.is_ascii_alphanumeric() || c == '_' || c == '-' || c == '.' { c } else { '_' })
                    .collect();
                let file = dir.join(format!("{}.ecproj", if safe.is_empty() { "cloud" } else { &safe }));
                match std::fs::write(&file, &bytes) {
                    Ok(()) => push(Event::Downloaded(file.to_string_lossy().to_string())),
                    Err(err) => push(Event::CloudFailed(format!("写文件失败: {err}"))),
                }
            }
            Ok(_) => push(Event::CloudFailed("云端工程是空的".to_string())),
            Err(err) => push(Event::CloudFailed(err)),
        }
    });
}

pub fn delete_project(token: String, id: String) {
    spawn(move || {
        let path = format!("/projects/{id}");
        match request("DELETE", &path, Some(&token), Some("{}")) {
            Ok((code, text)) => {
                if (200..300).contains(&code) {
                    push(Event::Deleted(id));
                } else {
                    push(Event::CloudFailed(cloud_hint(code, &json_or_null(&text))));
                }
            }
            Err(err) => push(Event::CloudFailed(err)),
        }
    });
}

/// 轮询账号状态（60 秒一次 / 切回前台一次）：用 `GET /me` 就够，后端没有 `/me/state`。
/// 被封返回 403 ACCOUNT_BANNED（message 里带原因），token 失效返回 401。
/// 网络错误静默——轮询不该打扰正在编辑的人。
pub fn check_state(token: String) {
    spawn(move || {
        // 2.6.0 起有 GET /me/state：不写审计、查询更少，正好适合每 60 秒轮询。
        // 老后端没有它（404）时退回 /me —— 两条路的判定都一样，只看状态码。
        let first = request("GET", "/me/state", Some(&token), None);
        let reply = match first {
            Ok((404, _)) => request("GET", "/me", Some(&token), None),
            other => other,
        };
        let (code, text) = match reply {
            Ok(pair) => pair,
            // 网络抖动、超时：什么都不做，下一轮再试。
            Err(_) => return,
        };
        let value = json_or_null(&text);
        if code == 403 {
            clear_token();
            push(Event::Banned(banned_text(&value)));
        } else if code == 401 {
            clear_token();
            if value["code"].as_str() == Some("ACCOUNT_BANNED") {
                push(Event::Banned(banned_text(&value)));
            } else {
                push(Event::SessionExpired);
            }
        }
        // 2xx：状态正常，什么都不用做。
    });
}

/// 封禁原因单独存一个文件：`clear_token()` 会把 `account.json` 整个删掉，
/// 但「为什么被踢下线」不该跟着 token 一起消失，重开 App 也要能说明白。
fn banned_path() -> std::path::PathBuf {
    config_dir().join("banned.txt")
}

pub fn save_banned(reason: &str) {
    let _ = std::fs::create_dir_all(config_dir());
    let _ = std::fs::write(banned_path(), reason);
}

pub fn load_banned() -> Option<String> {
    let text = std::fs::read_to_string(banned_path()).ok()?;
    let trimmed = text.trim();
    if trimmed.is_empty() {
        None
    } else {
        Some(trimmed.to_string())
    }
}

pub fn clear_banned() {
    let _ = std::fs::remove_file(banned_path());
}

/// 下载工程的落盘目录。
pub fn cloud_dir() -> std::path::PathBuf {
    config_dir().join("cloud")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn profile_reads_display_name_and_prefs() {
        let user = serde_json::json!({
            "display_name": "阿明",
            "prefs": { "profile": { "gender": "男", "birthday": "1990-01-02", "signature": "hi" } }
        });
        let profile = Profile::from_user(&user);
        assert_eq!(profile.nickname, "阿明");
        assert_eq!(profile.gender, "男");
        assert_eq!(profile.birthday, "1990-01-02");
        assert_eq!(profile.signature, "hi");
    }

    #[test]
    fn missing_fields_fall_back_to_empty() {
        let profile = Profile::from_user(&serde_json::json!({}));
        assert_eq!(profile, Profile::default());
    }

    #[test]
    fn login_hint_never_says_whether_the_account_exists() {
        assert_eq!(login_hint(401, &serde_json::Value::Null), "用户名或密码错误");
        assert_eq!(login_hint(0, &serde_json::Value::Null), "网络不可用，请检查网络后重试");
    }

    #[test]
    fn to_prefs_keeps_only_profile() {
        let profile = Profile { nickname: "n".into(), gender: "女".into(), birthday: "2000-01-01".into(), signature: "s".into() };
        let prefs = profile.to_prefs();
        assert_eq!(prefs["profile"]["gender"], "女");
        assert!(prefs["profile"].get("nickname").is_none());
    }
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    cargo = root / "crates/ui-egui/Cargo.toml"
    src = cargo.read_text(encoding="utf-8")
    if "ureq" not in src:
        if src.count(CARGO_ANCHOR) != 1:
            raise SystemExit(f"cargo anchor: {src.count(CARGO_ANCHOR)}")
        cargo.write_text(src.replace(CARGO_ANCHOR, CARGO_INSERT, 1), encoding="utf-8")
        print("cargo: ureq added")

    cloud = root / "crates/ui-egui/src/cloud.rs"
    if not cloud.exists():
        cloud.write_text(CLOUD_RS, encoding="utf-8")
        print("cloud.rs: written")

    lib = root / "crates/ui-egui/src/lib.rs"
    src = lib.read_text(encoding="utf-8")
    if "pub mod cloud;" not in src:
        if src.count(LIB_ANCHOR) != 1:
            raise SystemExit(f"lib anchor: {src.count(LIB_ANCHOR)}")
        lib.write_text(src.replace(LIB_ANCHOR, LIB_INSERT, 1), encoding="utf-8")
        print("lib.rs: cloud module registered")


if __name__ == "__main__":
    main()
