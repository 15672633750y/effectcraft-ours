package __PACKAGE__;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * Invisible trampoline for "Open with" / "Share to" on project and preset files.
 *
 * The app's real window is a NativeActivity with no intent plumbing, and the SAF recipe
 * machinery is far too heavy for what is needed here: receive the URI, drop the bytes into a
 * directory the Rust side already watches, then launch the normal launcher activity.
 */
public class ImportShim extends Activity {
    private static final String TARGET_DIR = "/storage/emulated/0/DCIM/EffectCraft/Import";

    @Override
    protected void onCreate(Bundle saved) {
        super.onCreate(saved);
        Uri uri = null;
        Intent intent = getIntent();
        if (intent != null) {
            if (intent.getData() != null) {
                uri = intent.getData();
            } else if (intent.getClipData() != null && intent.getClipData().getItemCount() > 0) {
                uri = intent.getClipData().getItemAt(0).getUri();
            }
        }
        if (uri != null) {
            copy(uri);
        }
        // Hand over to the real app, which picks the file up from TARGET_DIR.
        Intent launch = getPackageManager().getLaunchIntentForPackage(getPackageName());
        if (launch != null) {
            launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(launch);
        }
        finish();
    }

    private void copy(Uri uri) {
        String name = displayName(uri);
        if (name == null || name.isEmpty()) {
            name = "import-" + System.currentTimeMillis();
        }
        // Only the base name: the URI's last segment can contain %2F and friends.
        name = name.replaceAll("[\\\\/:*?\"<>|]", "_");
        File dir = new File(TARGET_DIR);
        if (!dir.exists() && !dir.mkdirs()) {
            return;
        }
        try (InputStream in = getContentResolver().openInputStream(uri)) {
            if (in == null) {
                return;
            }
            File outFile = new File(dir, name);
            try (OutputStream out = new FileOutputStream(outFile)) {
                byte[] buf = new byte[8192];
                int n;
                while ((n = in.read(buf)) > 0) {
                    out.write(buf, 0, n);
                }
            }
        } catch (Exception ignored) {
            // Nothing useful to report from a headless trampoline; the app shows the result.
        }
    }

    private String displayName(Uri uri) {
        try (android.database.Cursor c = getContentResolver().query(uri, null, null, null, null)) {
            if (c != null && c.moveToFirst()) {
                int idx = c.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME);
                if (idx >= 0) {
                    return c.getString(idx);
                }
            }
        } catch (Exception ignored) {
            // Fall through to the path segment.
        }
        String path = uri.getLastPathSegment();
        return path;
    }
}
