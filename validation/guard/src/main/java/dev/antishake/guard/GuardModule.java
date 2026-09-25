package dev.antishake.guard;

import android.app.Activity;
import android.content.ComponentName;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageInfo;
import android.hardware.Sensor;
import android.view.View;
import java.util.List;
import de.robv.android.xposed.IXposedHookLoadPackage;
import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage.LoadPackageParam;
import dev.antishake.policy.AdCloseRule;
import dev.antishake.policy.MotionPolicy;

/** The Xposed manager's user-selected scope is the only package selection authority. */
public final class GuardModule implements IXposedHookLoadPackage {
  @Override public void handleLoadPackage(LoadPackageParam app) {
    if (app.packageName.equals("dev.antishake.guard") || app.appInfo == null
        || (app.appInfo.flags & ApplicationInfo.FLAG_SYSTEM) != 0) return;

    try {
      installSensorHooks(app);
      // Diagnostic marker only. Fixture still uses the real SensorManager to detect motion.
      if (app.packageName.equals(AdCloseRule.PACKAGE)) {
        XposedHelpers.findAndHookMethod("dev.antishake.fixture.Probe", app.classLoader,
            "hookActive", new XC_MethodHook() {
              @Override protected void afterHookedMethod(MethodHookParam param) {
                param.setResult(true);
              }
            });
        installCloseHook();
      }
      XposedBridge.log("AntiShake: Java hooks installed for " + app.packageName);
    } catch (Throwable failure) {
      XposedBridge.log("AntiShake: installation incomplete for " + app.packageName);
      XposedBridge.log(failure);
    }
  }

  private void installSensorHooks(LoadPackageParam app) throws Throwable {
    HookRollback rollback = new HookRollback();
    try {
      installSensorHooks(app, rollback);
    } catch (Throwable failure) {
      rollback.rollback(failure);
      throw failure;
    }
  }

  private void installSensorHooks(LoadPackageParam app, HookRollback rollback) {
    Class<?> manager = XposedHelpers.findClass("android.hardware.SystemSensorManager", app.classLoader);
    // Derived from Sensor Disabler's RemoveSensorModificationMethod (Wardell Bagby, MIT).
    // Copy the list before filtering; never mutate Android's shared sensor inventory.
    XC_MethodHook.Unhook listHook = XposedHelpers.findAndHookMethod(manager, "getFullSensorList", new XC_MethodHook() {
      @Override @SuppressWarnings("unchecked")
      protected void afterHookedMethod(MethodHookParam param) {
        if (!param.hasThrowable() && param.getResult() instanceof List) {
          param.setResult(MotionPolicy.visibleSensors((List<Sensor>) param.getResult(), Sensor::getType, true));
        }
      }
    });
    rollback.add(listHook::unhook);
    XC_MethodHook dynamicCallback = new XC_MethodHook() {
      @Override @SuppressWarnings("unchecked")
      protected void afterHookedMethod(MethodHookParam param) {
        if (!param.hasThrowable() && param.getResult() instanceof List) {
          param.setResult(MotionPolicy.visibleSensors((List<Sensor>) param.getResult(), Sensor::getType, true));
        }
      }
    };
    rollback.installMethods(manager, "getFullDynamicSensorList",
        method -> XposedBridge.hookMethod(method, dynamicCallback)::unhook);
    // Defense for sensor objects obtained through another Java path or cached by a library.
    for (String method : new String[] {"registerListenerImpl", "requestTriggerSensorImpl"}) {
      XC_MethodHook callback = new XC_MethodHook() {
        @Override protected void beforeHookedMethod(MethodHookParam param) {
          for (Object argument : param.args) {
            if (argument instanceof Sensor && MotionPolicy.blocks(((Sensor) argument).getType())) {
              param.setResult(false);
              return;
            }
          }
        }
      };
      int installed = rollback.installMethods(manager, method,
          target -> XposedBridge.hookMethod(target, callback)::unhook);
      if (installed == 0) throw new IllegalStateException("Missing hook: " + method);
    }
  }

  private void installCloseHook() {
    XposedHelpers.findAndHookMethod(Activity.class, "onPostResume", new XC_MethodHook() {
      @Override protected void afterHookedMethod(MethodHookParam param) {
        Activity activity = (Activity) param.thisObject;
        if (!AdCloseRule.ACTIVITY.equals(activity.getClass().getName())) return;
        try {
          PackageInfo info = activity.getPackageManager().getPackageInfo(activity.getPackageName(), 0);
          if (!AdCloseRule.PACKAGE.equals(activity.getPackageName()) || info.versionCode != 1) return;
          activity.getWindow().getDecorView().post(() -> closeFixtureAd(activity, 0));
        } catch (Exception failure) { XposedBridge.log(failure); }
      }
    });
  }

  private void closeFixtureAd(Activity activity, int attempt) {
    if (activity.isFinishing() || activity.isDestroyed()) return;
    int id = activity.getResources().getIdentifier("close_ad", "id", activity.getPackageName());
    View button = id == 0 ? null : activity.findViewById(id);
    boolean markedButton = button != null && button.isShown() && button.isEnabled()
        && button.isClickable() && AdCloseRule.MARKER.equals(button.getTag());
    ComponentName parent = activity.getCallingActivity();
    boolean knownParent = parent != null && AdCloseRule.PACKAGE.equals(parent.getPackageName())
        && AdCloseRule.PARENT.equals(parent.getClassName());
    AdCloseRule.Action action = AdCloseRule.decide(activity.getPackageName(), 1,
        activity.getClass().getName(), markedButton, knownParent, attempt >= 20, activity.hasWindowFocus());
    if (action == AdCloseRule.Action.CLOSE && button.performClick()) return;
    if (action == AdCloseRule.Action.RETURN) {
      activity.setResult(Activity.RESULT_CANCELED);
      activity.finish();
      return;
    }
    if ((action == AdCloseRule.Action.RETRY || action == AdCloseRule.Action.CLOSE) && attempt < 20)
      activity.getWindow().getDecorView()
        .postDelayed(() -> closeFixtureAd(activity, attempt + 1), 100);
  }
}
