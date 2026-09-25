package dev.antishake.fixture;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public final class MainActivity extends Activity {
  @Override public void onCreate(Bundle state) {
    super.onCreate(state);
    if (state == null) Probe.reset(this);
    LinearLayout root = new LinearLayout(this);
    root.setOrientation(LinearLayout.VERTICAL);
    root.setPadding(24, 64, 24, 24);
    TextView title = new TextView(this);
    title.setText(getString(R.string.app_name) + "\n真实 Hook：" + Probe.hookActive());
    title.setTextSize(22);
    root.addView(title);
    for (String scenario : new String[] {"probe", "ad", "delayed", "missing"}) {
      Button button = new Button(this);
      button.setText("测试：" + scenario);
      button.setOnClickListener(view -> open(scenario));
      root.addView(button);
    }
    Button normal = new Button(this);
    normal.setText("关闭 / 跳过（普通页面，不能被自动点击）");
    normal.setId(R.id.close_ad);
    normal.setTag("antishake:advertisement:v1");
    normal.setOnClickListener(view -> Probe.increment(this, "normalClicks"));
    root.addView(normal);
    setContentView(root);
    String scenario = getIntent().getStringExtra("case");
    if (state == null && scenario != null && !scenario.equals("normal")) open(scenario);
  }

  private void open(String scenario) {
    Probe.reset(this);
    Class<?> target = scenario.equals("probe") ? ProbeActivity.class : AdActivity.class;
    startActivityForResult(new Intent(this, target).putExtra("case", scenario), 1);
  }

  @Override protected void onActivityResult(int request, int result, Intent data) {
    super.onActivityResult(request, result, data);
    Probe.put(this, "close", result == RESULT_OK ? "CLOSED" : "RETURNED");
    Probe.put(this, "screen", "MAIN");
  }
}
