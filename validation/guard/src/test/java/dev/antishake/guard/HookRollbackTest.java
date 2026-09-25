package dev.antishake.guard;

import static org.junit.Assert.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.junit.Test;

public class HookRollbackTest {
  @Test public void failedInstallUndoesEveryRegisteredHookInReverseOrderOnce() {
    HookRollback rollback = new HookRollback();
    List<String> removed = new ArrayList<>();
    rollback.add(() -> removed.add("list"));
    rollback.add(() -> removed.add("registration"));
    rollback.rollback(new IllegalStateException("missing trigger method"));
    rollback.rollback(new IllegalStateException("repeated cleanup"));
    assertEquals(Arrays.asList("registration", "list"), removed);
  }

  @Test public void oneCleanupFailureDoesNotPreventOtherHooksFromBeingRemoved() {
    HookRollback rollback = new HookRollback();
    List<String> removed = new ArrayList<>();
    RuntimeException cleanup = new IllegalStateException("cannot unhook");
    Throwable install = new IllegalStateException("install failed");
    rollback.add(() -> removed.add("first"));
    rollback.add(() -> { throw cleanup; });
    rollback.rollback(install);
    assertEquals(Arrays.asList("first"), removed);
    assertArrayEquals(new Throwable[] {cleanup}, install.getSuppressed());
  }

  @Test public void overloadFailureLeavesEarlierSuccessfulRegistrationsAvailableForRollback() {
    HookRollback rollback = new HookRollback();
    List<String> events = new ArrayList<>();
    RuntimeException failure = new IllegalStateException("second overload failed");
    try {
      rollback.installMethods(Overloaded.class, "listen", method -> {
        if (events.size() == 1) throw failure;
        events.add("installed");
        return () -> events.add("removed");
      });
      fail("Second overload should fail registration");
    } catch (RuntimeException caught) {
      assertSame(failure, caught);
      rollback.rollback(caught);
    }
    assertEquals(Arrays.asList("installed", "removed"), events);
  }

  static final class Overloaded {
    void listen() {}
    void listen(int rate) {}
    void unrelated() { throw new AssertionError("not a registration target"); }
  }
}
