package dev.antishake.policy;

import static org.junit.Assert.assertEquals;
import static dev.antishake.policy.AdCloseRule.*;
import org.junit.Test;

public class AdCloseRuleTest {
  @Test public void closesOnlyTheRecognizedFixtureAd() {
    assertEquals(Action.CLOSE, decide(PACKAGE, 1, ACTIVITY, true, true, false));
  }

  @Test public void ignoresNormalPagesOtherAppsAndUnknownVersions() {
    assertEquals(Action.NONE, decide(PACKAGE, 1, PARENT, true, true, true));
    assertEquals(Action.NONE, decide("dev.antishake.fixture.control", 1, ACTIVITY, true, true, true));
    assertEquals(Action.NONE, decide(PACKAGE, 2, ACTIVITY, true, true, true));
    assertEquals(Action.NONE, decide(PACKAGE, 1, ACTIVITY, false, false, true));
  }

  @Test public void waitsForDelayedCloseButtonThenReturnsOnlyToVerifiedParent() {
    assertEquals(Action.RETRY, decide(PACKAGE, 1, ACTIVITY, false, true, false));
    assertEquals(Action.RETURN, decide(PACKAGE, 1, ACTIVITY, false, true, true));
    assertEquals(Action.CLOSE, decide(PACKAGE, 1, ACTIVITY, true, true, true));
  }

  @Test public void initialLackOfFocusRetriesWithoutClickingOrReturning() {
    assertEquals(Action.RETRY, decide(PACKAGE, 1, ACTIVITY, true, true, false, false));
    assertEquals(Action.NONE, decide(PACKAGE, 1, ACTIVITY, true, true, true, false));
    assertEquals(Action.CLOSE, decide(PACKAGE, 1, ACTIVITY, true, true, false, true));
  }

  @Test public void matchingButtonDoesNotAuthorizeActionsFromAnUnknownParent() {
    assertEquals(Action.NONE, decide(PACKAGE, 1, ACTIVITY, true, false, false, true));
    assertEquals(Action.NONE, decide(PACKAGE, 1, ACTIVITY, false, false, false, false));
  }
}
