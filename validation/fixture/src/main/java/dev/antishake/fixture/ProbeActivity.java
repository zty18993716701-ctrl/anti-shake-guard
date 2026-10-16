package dev.antishake.fixture;

import android.app.Activity;
import android.content.Intent;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

/** Real sensor listener shared by the moving-ad scenario and the non-closing probe. */
public class ProbeActivity extends Activity implements SensorEventListener {
  protected LinearLayout root;
  private SensorManager sensors;
  private TextView status;
  private float[] previousAcceleration;
  private boolean navigated;

  @Override public void onCreate(Bundle state) {
    super.onCreate(state);
    sensors = (SensorManager) getSystemService(SENSOR_SERVICE);
    root = new LinearLayout(this);
    root.setOrientation(LinearLayout.VERTICAL);
    root.setPadding(24, 64, 24, 24);
    status = new TextView(this);
    status.setId(R.id.probe_status);
    status.setTextSize(20);
    root.addView(status);
    Button refresh = new Button(this);
    refresh.setId(R.id.refresh_probe);
    refresh.setText("刷新探针读数");
    refresh.setOnClickListener(view -> updateStatus());
    root.addView(refresh);
    setContentView(root);
    Probe.put(this, "screen", getClass() == ProbeActivity.class ? "PROBE" : "AD");
  }

  @Override protected void onResume() {
    super.onResume();
    Probe.increment(this, "resumes");
    int available = 0;
    for (int type : new int[] {Sensor.TYPE_ACCELEROMETER, Sensor.TYPE_GYROSCOPE}) {
      Sensor sensor = sensors.getDefaultSensor(type);
      if (sensor != null) {
        available++;
        sensors.registerListener(this, sensor, SensorManager.SENSOR_DELAY_GAME);
      }
    }
    Probe.put(this, "sensorCount", Integer.toString(available));
    Sensor light = sensors.getDefaultSensor(Sensor.TYPE_LIGHT);
    Probe.put(this, "lightAvailable", Boolean.toString(light != null));
    if (light != null) sensors.registerListener(this, light, SensorManager.SENSOR_DELAY_NORMAL);
    updateStatus();
  }

  @Override protected void onPause() {
    sensors.unregisterListener(this);
    super.onPause();
  }

  @Override public void onSensorChanged(SensorEvent event) {
    if (navigated || isFinishing()) return;
    if (event.sensor.getType() == Sensor.TYPE_LIGHT) {
      Probe.increment(this, "lightEvents");
      Probe.put(this, "lastLight", Float.toString(event.values[0]));
      return;
    }
    Probe.increment(this, "events");
    boolean moved = false;
    if (event.sensor.getType() == Sensor.TYPE_ACCELEROMETER) {
      if (previousAcceleration != null) {
        double delta = 0;
        for (int axis = 0; axis < 3; axis++) delta += Math.pow(event.values[axis] - previousAcceleration[axis], 2);
        moved = delta > 16;
      }
      previousAcceleration = event.values.clone();
    } else if (event.sensor.getType() == Sensor.TYPE_GYROSCOPE) {
      moved = Math.abs(event.values[0]) + Math.abs(event.values[1]) + Math.abs(event.values[2]) > 2;
    }
    if (moved) {
      navigated = true;
      Probe.put(this, "navigated", "true");
      startActivity(new Intent(this, TargetActivity.class));
    }
  }

  private void updateStatus() {
    status.setText("模拟广告 / 传感器探针\n真实 Hook：" + Probe.hookActive()
        + "\n可见加速度计/陀螺仪：" + Probe.state.getProperty("sensorCount")
        + "\n收到运动事件：" + Probe.state.getProperty("events")
        + "\n读数为快照，点击刷新更新。"
        + "\n移动或旋转模拟设备，未保护时将跳转。");
  }

  @Override public void onAccuracyChanged(Sensor sensor, int accuracy) {}
}
