package dev.antishake.guard;

import static org.junit.Assert.*;
import android.view.View;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageInfo;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.TextView;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.Shadows;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = {28, 35})
public class SetupTest {
  @Test public void missingFixturesDisableTestEntryAndNeverClaimProtection() {
    try (ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class).setup()) {
      View root = controller.get().findViewById(android.R.id.content);
      Button protectedTest = (Button) findText(root, "打开保护组探针");
      assertNotNull("Setup must offer a direct protected fixture entry", protectedTest);
      assertFalse(protectedTest.isEnabled());
      assertNotNull(findText(root, "保护组：未安装"));
      assertNotNull(findText(root, "拦截效果：未验证（安装完成不代表保护生效）"));
    }
  }

  @Test public void matchingFixtureOpensOnlyItsExplicitProbeWithoutClaimingSuccess() {
    installProtected(1);
    try (ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class).setup()) {
      View root = controller.get().findViewById(android.R.id.content);
      Button open = (Button) findText(root, "打开保护组探针");
      assertTrue(open.isEnabled());
      open.performClick();
      Intent intent = Shadows.shadowOf(controller.get()).getNextStartedActivity();
      assertEquals("dev.antishake.fixture.protectedapp", intent.getComponent().getPackageName());
      assertEquals("dev.antishake.fixture.MainActivity", intent.getComponent().getClassName());
      assertEquals("probe", intent.getStringExtra("case"));
      assertNotNull(findText(root, "拦截效果：未验证（安装完成不代表保护生效）"));
    }
  }

  @Test public void fixtureUpdatedWhileSetupIsOpenCannotLaunchThroughStaleButton() {
    installProtected(1);
    try (ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class).setup()) {
      View root = controller.get().findViewById(android.R.id.content);
      installProtected(2);
      findText(root, "打开保护组探针").performClick();
      assertNull(Shadows.shadowOf(controller.get()).getNextStartedActivity());
    }
  }

  private static void installProtected(int version) {
    PackageInfo info = new PackageInfo();
    info.packageName = "dev.antishake.fixture.protectedapp";
    info.versionCode = version;
    info.applicationInfo = new ApplicationInfo();
    info.applicationInfo.packageName = info.packageName;
    info.applicationInfo.enabled = true;
    Shadows.shadowOf(RuntimeEnvironment.getApplication().getPackageManager()).installPackage(info);
  }

  private static TextView findText(View view, String text) {
    if (view instanceof TextView && text.contentEquals(((TextView) view).getText())) return (TextView) view;
    if (view instanceof ViewGroup) {
      ViewGroup group = (ViewGroup) view;
      for (int i = 0; i < group.getChildCount(); i++) {
        TextView found = findText(group.getChildAt(i), text);
        if (found != null) return found;
      }
    }
    return null;
  }
}
