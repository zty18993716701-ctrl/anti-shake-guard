package dev.antishake.policy;

import java.util.ArrayList;
import java.util.List;
import java.util.function.ToIntFunction;

/** Sensor type IDs are Android's public Sensor.TYPE_* constants. */
public final class MotionPolicy {
  private MotionPolicy() {}

  public static boolean blocks(int sensorType) {
    switch (sensorType) {
      case 1:  // Accelerometer
      case 2:  // Magnetic field (can infer rotation)
      case 3:  // Deprecated orientation
      case 4:  // Gyroscope
      case 9:  // Gravity
      case 10: // Linear acceleration
      case 11: // Rotation vector
      case 14: // Uncalibrated magnetic field
      case 15: // Game rotation vector
      case 16: // Uncalibrated gyroscope
      case 17: // Significant motion
      case 18: // Step detector
      case 19: // Step counter
      case 20: // Geomagnetic rotation vector
      case 22: // Tilt detector
      case 23: // Wake gesture
      case 24: // Glance gesture
      case 25: // Pick-up gesture
      case 26: // Wrist tilt gesture
      case 29: // Stationary detect
      case 30: // Motion detect
      case 35: // Uncalibrated accelerometer
      case 36: // Hinge angle
        return true;
      default:
        return false;
    }
  }

  public static <T> List<T> visibleSensors(List<T> sensors, ToIntFunction<T> type,
      boolean protectedApp) {
    List<T> visible = new ArrayList<>();
    for (T sensor : sensors) {
      if (!protectedApp || !blocks(type.applyAsInt(sensor))) visible.add(sensor);
    }
    return visible;
  }
}
