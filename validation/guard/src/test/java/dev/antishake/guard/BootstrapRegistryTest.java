package dev.antishake.guard;

import static org.junit.Assert.assertEquals;
import java.util.Arrays;
import java.util.concurrent.CopyOnWriteArraySet;
import org.junit.Test;

public class BootstrapRegistryTest {
  @Test public void standardRuntimeRegistryReportsRegisteredCallbackCount() {
    CopyOnWriteArraySet<String> callbacks = new CopyOnWriteArraySet<>(Arrays.asList("first", "second", "first"));
    assertEquals(2, GuardModule.registeredCallbackCount(callbacks));
  }

  @Test public void emptyRuntimeRegistryReportsZeroWithoutBecomingUnavailable() {
    assertEquals(0, GuardModule.registeredCallbackCount(new CopyOnWriteArraySet<>()));
  }
}
