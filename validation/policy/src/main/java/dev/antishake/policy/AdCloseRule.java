package dev.antishake.policy;

/** A single versioned rule for our controlled fixture, never a generic text matcher. */
public final class AdCloseRule {
  public static final String PACKAGE = "dev.antishake.fixture.protectedapp";
  public static final String ACTIVITY = "dev.antishake.fixture.AdActivity";
  public static final String PARENT = "dev.antishake.fixture.MainActivity";
  public static final String MARKER = "antishake:advertisement:v1";
  public enum Action { CLOSE, RETURN, RETRY, NONE }

  private AdCloseRule() {}

  public static Action decide(String packageName, long version, String activity,
      boolean markedCloseButton, boolean verifiedParent, boolean attemptsExhausted) {
    return decide(packageName, version, activity, markedCloseButton, verifiedParent, attemptsExhausted, true);
  }

  public static Action decide(String packageName, long version, String activity,
      boolean markedCloseButton, boolean verifiedParent, boolean attemptsExhausted, boolean focused) {
    if (!PACKAGE.equals(packageName) || version != 1 || !ACTIVITY.equals(activity) || !verifiedParent) {
      return Action.NONE;
    }
    if (!focused) return attemptsExhausted ? Action.NONE : Action.RETRY;
    if (markedCloseButton) return Action.CLOSE;
    if (!attemptsExhausted) return Action.RETRY;
    return Action.RETURN;
  }
}
