package dev.antishake.fixture;

import static org.junit.Assert.*;
import android.app.Activity;
import android.content.Intent;
import android.content.Context;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorManager;
import android.os.Looper;
import android.widget.Button;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.Shadows;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.LooperMode;
import org.robolectric.shadows.ShadowSensor;
import org.robolectric.shadows.ShadowSensorManager;
import java.time.Duration;

/** Harness checks; these deliberately do not claim to run the Xposed module. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = {28, 35})
@LooperMode(LooperMode.Mode.PAUSED)
public class FixtureTest {
  @Test public void registeredMotionListenerNavigatesButLightDoesNot() {
    Probe.reset(RuntimeEnvironment.getApplication());
    SensorManager manager = (SensorManager) RuntimeEnvironment.getApplication().getSystemService(Context.SENSOR_SERVICE);
    ShadowSensorManager virtual = Shadows.shadowOf(manager);
    Sensor acceleration = ShadowSensor.newInstance(Sensor.TYPE_ACCELEROMETER);
    Sensor light = ShadowSensor.newInstance(Sensor.TYPE_LIGHT);
    virtual.addSensor(acceleration);
    virtual.addSensor(light);
    try (ActivityController<ProbeActivity> controller = Robolectric.buildActivity(ProbeActivity.class).setup()) {
      assertTrue(virtual.hasListener(controller.get(), acceleration));
      assertTrue(virtual.hasListener(controller.get(), light));
      SensorEvent brightness = ShadowSensorManager.createSensorEvent(1);
      brightness.sensor = light;
      brightness.values[0] = 123;
      virtual.sendSensorEventToListeners(brightness, light);
      assertEquals("123.0", Probe.state.getProperty("lastLight"));
      assertEquals("false", Probe.state.getProperty("navigated"));

      SensorEvent movement = ShadowSensorManager.createSensorEvent(3);
      movement.sensor = acceleration;
      movement.values[2] = 9.81f;
      virtual.sendSensorEventToListeners(movement, acceleration);
      assertEquals("false", Probe.state.getProperty("navigated"));
      movement.values[0] = 20;
      virtual.sendSensorEventToListeners(movement, acceleration);
      assertEquals("true", Probe.state.getProperty("navigated"));
      Intent destination = Shadows.shadowOf(controller.get()).getNextStartedActivity();
      assertEquals(TargetActivity.class.getName(), destination.getComponent().getClassName());
      controller.pause();
      assertFalse(virtual.hasListener(controller.get()));
    }
  }

  @Test public void normalPageHasNoAutomaticNavigationOrClicks() {
    try (ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class).setup()) {
      Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(3));
      assertFalse(Probe.hookActive());
      assertEquals("MAIN", Probe.state.getProperty("screen"));
      assertEquals("0", Probe.state.getProperty("normalClicks"));
      assertNull(Shadows.shadowOf(controller.get()).getNextStartedActivity());
    }
  }

  @Test public void recreatingLauncherDoesNotOpenTheRequestedScenarioTwice() {
    Intent launch = new Intent(RuntimeEnvironment.getApplication(), MainActivity.class).putExtra("case", "ad");
    try (ActivityController<MainActivity> controller = Robolectric.buildActivity(MainActivity.class, launch).setup()) {
      assertNotNull(Shadows.shadowOf(controller.get()).getNextStartedActivity());
      controller.recreate();
      assertNull(Shadows.shadowOf(controller.get()).getNextStartedActivity());
    }
  }

  @Test public void adCloseButtonFinishesAdWithSuccessfulResult() {
    Probe.reset(RuntimeEnvironment.getApplication());
    try (ActivityController<AdActivity> controller = Robolectric.buildActivity(AdActivity.class).setup()) {
      Button close = controller.get().findViewById(R.id.close_ad);
      assertEquals("antishake:advertisement:v1", close.getTag());
      assertTrue(close.performClick());
      assertTrue(controller.get().isFinishing());
      assertEquals(Activity.RESULT_OK, Shadows.shadowOf(controller.get()).getResultCode());
      assertNull(Shadows.shadowOf(controller.get()).getNextStartedActivity());
    }
  }

  @Test public void delayedCloseControlBecomesAvailableAndMissingControlStaysMissing() {
    Probe.reset(RuntimeEnvironment.getApplication());
    Intent delayed = new Intent(RuntimeEnvironment.getApplication(), AdActivity.class).putExtra("case", "delayed");
    try (ActivityController<AdActivity> controller = Robolectric.buildActivity(AdActivity.class, delayed).setup().visible()) {
      Button close = controller.get().findViewById(R.id.close_ad);
      assertFalse(close.isEnabled());
      Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(700));
      assertTrue(close.isEnabled());
    }
    Intent missing = new Intent(RuntimeEnvironment.getApplication(), AdActivity.class).putExtra("case", "missing");
    try (ActivityController<AdActivity> controller = Robolectric.buildActivity(AdActivity.class, missing).setup()) {
      assertNull(controller.get().findViewById(R.id.close_ad));
      assertFalse(controller.get().isFinishing());
    }
  }
}
