package dev.antishake.guard;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.provider.Settings;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/** Installation checks are not evidence that another process has working Xposed hooks. */
public final class MainActivity extends Activity {
  private static final String PROTECTED = "dev.antishake.fixture.protectedapp";
  private static final String CONTROL = "dev.antishake.fixture.control";
  private LinearLayout content;
  private TextView message;

  @Override public void onCreate(Bundle state) {
    super.onCreate(state);
    ScrollView scroll = new ScrollView(this);
    content = new LinearLayout(this);
    content.setOrientation(LinearLayout.VERTICAL);
    int padding = (int) (24 * getResources().getDisplayMetrics().density);
    content.setPadding(padding, padding * 2, padding, padding);
    scroll.addView(content);
    setContentView(scroll);
  }

  @Override protected void onResume() {
    super.onResume();
    content.removeAllViews();
    text(R.string.setup_title).setTextSize(24);
    text(R.string.setup_warning);
    text(R.string.setup_steps);
    fixture(PROTECTED, R.string.protected_label, R.string.open_protected);
    fixture(CONTROL, R.string.control_label, R.string.open_control);
    text(R.string.unverified);
    text(R.string.check_instructions);
    button(R.string.open_ad, usable(PROTECTED), () -> openFixture(PROTECTED, "ad"));
    button(R.string.open_normal, usable(PROTECTED), () -> openFixture(PROTECTED, "normal"));
    text(R.string.rollback_instructions);
    button(R.string.open_fixture_settings, usable(PROTECTED), () -> launch(
        new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + PROTECTED))));
    text(R.string.credits);
    message = text(R.string.setup_ready);
    message.setAccessibilityLiveRegion(TextView.ACCESSIBILITY_LIVE_REGION_POLITE);
  }

  private void fixture(String packageName, int label, int buttonLabel) {
    TextView status = new TextView(this);
    status.setText(getString(label) + "：" + getString(installationStatus(packageName)));
    content.addView(status);
    button(buttonLabel, usable(packageName), () -> openFixture(packageName, "probe"));
  }

  private boolean usable(String packageName) { return installationStatus(packageName) == R.string.installed; }

  private int installationStatus(String packageName) {
    try {
      PackageInfo info = getPackageManager().getPackageInfo(packageName, 0);
      if (info.applicationInfo == null || !info.applicationInfo.enabled) return R.string.disabled;
      return info.versionCode == 1 ? R.string.installed : R.string.unsupported;
    } catch (PackageManager.NameNotFoundException missing) { return R.string.missing; }
  }

  private void openFixture(String packageName, String scenario) {
    if (!usable(packageName)) {
      message.setText(R.string.launch_failed);
      return;
    }
    launch(new Intent().setClassName(packageName, "dev.antishake.fixture.MainActivity")
        .putExtra("case", scenario));
  }

  private void launch(Intent intent) {
    try { startActivity(intent); }
    catch (ActivityNotFoundException | SecurityException unavailable) {
      message.setText(R.string.launch_failed);
    }
  }

  private TextView text(int label) {
    TextView view = new TextView(this);
    view.setText(label);
    view.setTextSize(16);
    view.setPadding(0, 12, 0, 12);
    content.addView(view);
    return view;
  }

  private void button(int label, boolean enabled, Runnable action) {
    Button view = new Button(this);
    view.setText(label);
    view.setEnabled(enabled);
    view.setOnClickListener(ignored -> action.run());
    content.addView(view);
  }
}
