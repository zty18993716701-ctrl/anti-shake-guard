package dev.antishake.fixture;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;

public final class TargetActivity extends Activity {
  @Override public void onCreate(Bundle state) {
    super.onCreate(state);
    Probe.put(this, "screen", "TARGET");
    TextView view = new TextView(this);
    view.setPadding(24, 64, 24, 24);
    view.setTextSize(24);
    view.setText("已因运动跳转到广告目标页\n对照组应出现此页；保护组不应出现。");
    setContentView(view);
  }
}
