package dev.antishake.policy;

import static org.junit.Assert.*;
import java.util.Arrays;
import java.util.List;
import org.junit.Test;

public class MotionPolicyTest {
  @Test public void selectedAppCannotDiscoverMotionButKeepsLightAndProximity() {
    List<Integer> sensors = Arrays.asList(1, 4, 5, 8, 9, 10, 11);
    assertEquals(Arrays.asList(5, 8), MotionPolicy.visibleSensors(sensors, i -> i, true));
    assertEquals(Arrays.asList(1, 4, 5, 8, 9, 10, 11), sensors);
  }

  @Test public void unselectedAppRetainsItsEntireSensorList() {
    List<Integer> sensors = Arrays.asList(1, 4, 5, 8, 9, 10, 11, 16, 35);
    assertEquals(sensors, MotionPolicy.visibleSensors(sensors, i -> i, false));
  }

  @Test public void alternateMotionSourcesCannotBypassProtection() {
    // Magnetic/orientation fusion, uncalibrated, game, trigger and step sensors.
    int[] motion = {2, 3, 14, 15, 16, 17, 18, 19, 20, 22, 23, 24, 25, 26, 29, 30, 35, 36};
    for (int type : motion) assertTrue("Must block sensor type " + type, MotionPolicy.blocks(type));
    for (int type : new int[] {5, 6, 7, 8, 12, 13, 21, 27, 28, 31, 34, 65536}) {
      assertFalse("Must preserve non-motion/unknown type " + type, MotionPolicy.blocks(type));
    }
  }
}
