package dev.antishake.fixture;

import android.os.Bundle;
import android.widget.Button;

public final class AdActivity extends ProbeActivity {
  @Override public void onCreate(Bundle state) {
    super.onCreate(state);
    String scenario = getIntent().getStringExtra("case");
    if ("missing".equals(scenario)) return;
    Button close = new Button(this);
    close.setId(R.id.close_ad);
    close.setTag("antishake:advertisement:v1");
    close.setText("关闭广告");
    close.setOnClickListener(view -> { setResult(RESULT_OK); finish(); });
    if ("delayed".equals(scenario)) {
      close.setEnabled(false);
      close.postDelayed(() -> close.setEnabled(true), 600);
    }
    root.addView(close);
  }
}
