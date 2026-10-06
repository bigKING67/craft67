package dev.designcraft.runtimeevidence;

import android.app.Activity;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public final class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        int padding = Math.round(24 * getResources().getDisplayMetrics().density);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_VERTICAL);
        root.setPadding(padding, padding, padding, padding);

        TextView title = new TextView(this);
        title.setText("Native runtime evidence");
        title.setTextSize(28);
        title.setContentDescription("Native runtime evidence title");

        TextView status = new TextView(this);
        status.setText(Settings.Global.getFloat(getContentResolver(), Settings.Global.ANIMATOR_DURATION_SCALE, 1f) == 0f
                ? "Remove animations enabled"
                : "Remove animations disabled");
        status.setTextSize(18);
        status.setContentDescription("Runtime status");

        Button action = new Button(this);
        action.setText("Confirm runtime");
        action.setMinHeight(Math.round(48 * getResources().getDisplayMetrics().density));
        action.setContentDescription("Confirm native runtime");
        action.setOnClickListener(view -> status.setText("Runtime interaction confirmed"));

        root.addView(title, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        root.addView(status, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        root.addView(action, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        setContentView(root);
    }
}
