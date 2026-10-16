package dev.antishake.fixture;

import android.content.Context;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.Properties;

/** Debug fixture evidence read with adb run-as; never used to simulate sensor suppression. */
public final class Probe {
  static final Properties state = new Properties();
  private Probe() {}

  public static boolean hookActive() { return false; }

  static void reset(Context context) {
    state.clear();
    state.setProperty("hook", Boolean.toString(hookActive()));
    state.setProperty("events", "0");
    state.setProperty("resumes", "0");
    state.setProperty("navigated", "false");
    state.setProperty("normalClicks", "0");
    state.setProperty("close", "NONE");
    state.setProperty("sensorCount", "0");
    state.setProperty("lightAvailable", "false");
    state.setProperty("lightEvents", "0");
    state.setProperty("lastLight", "-1");
    put(context, "screen", "MAIN");
  }

  static void increment(Context context, String key) {
    put(context, key, Integer.toString(Integer.parseInt(state.getProperty(key, "0")) + 1));
  }

  static void put(Context context, String key, String value) {
    state.setProperty(key, value);
    File pending = new File(context.getFilesDir(), "probe.tmp");
    try (FileOutputStream output = new FileOutputStream(pending)) {
      state.store(output, "Test fixture evidence");
    } catch (IOException failure) { throw new IllegalStateException(failure); }
    if (!pending.renameTo(new File(context.getFilesDir(), "probe.properties"))) {
      throw new IllegalStateException("Cannot publish fixture evidence");
    }
  }
}
