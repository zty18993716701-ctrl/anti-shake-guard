package dev.antishake.guard;

import java.util.ArrayList;
import java.util.List;
import java.lang.reflect.Method;
import java.util.function.Function;

/** Undo only hooks installed by this attempt if a required registration fails. */
final class HookRollback {
  private final List<Runnable> removals = new ArrayList<>();

  void add(Runnable removal) { removals.add(removal); }

  int installMethods(Class<?> type, String name, Function<Method, Runnable> installer) {
    int installed = 0;
    for (Method method : type.getDeclaredMethods()) {
      if (method.getName().equals(name)) {
        add(installer.apply(method));
        installed++;
      }
    }
    return installed;
  }

  void rollback(Throwable cause) {
    for (int i = removals.size() - 1; i >= 0; i--) {
      try { removals.get(i).run(); }
      catch (Throwable cleanup) {
        if (cleanup != cause) cause.addSuppressed(cleanup);
      }
    }
    removals.clear();
  }
}
