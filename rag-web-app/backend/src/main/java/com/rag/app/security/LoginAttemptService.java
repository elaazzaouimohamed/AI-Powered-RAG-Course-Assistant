package com.rag.app.security;

import org.springframework.stereotype.Component;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Protection anti brute-force basique : verrouille un identifiant (username normalisé)
 * après plusieurs échecs de connexion consécutifs, pendant une durée limitée.
 * En mémoire — suffisant pour une seule instance ; à déplacer dans Redis si on scale
 * horizontalement.
 */
@Component
public class LoginAttemptService {

    private static final int MAX_ATTEMPTS = 5;
    private static final long LOCKOUT_MINUTES = 15;

    private record Attempt(int count, Instant lockedUntil) {}

    private final ConcurrentHashMap<String, Attempt> attempts = new ConcurrentHashMap<>();

    public void loginFailed(String key) {
        attempts.compute(key.toLowerCase(), (k, prev) -> {
            int count = (prev == null ? 0 : prev.count()) + 1;
            Instant lockedUntil = count >= MAX_ATTEMPTS
                    ? Instant.now().plus(LOCKOUT_MINUTES, ChronoUnit.MINUTES)
                    : null;
            return new Attempt(count, lockedUntil);
        });
    }

    public void loginSucceeded(String key) {
        attempts.remove(key.toLowerCase());
    }

    public boolean isBlocked(String key) {
        return secondsUntilUnlocked(key) > 0;
    }

    public long secondsUntilUnlocked(String key) {
        var a = attempts.get(key.toLowerCase());
        if (a == null || a.lockedUntil() == null) return 0;
        long secs = Instant.now().until(a.lockedUntil(), ChronoUnit.SECONDS);
        if (secs <= 0) {
            attempts.remove(key.toLowerCase());
            return 0;
        }
        return secs;
    }
}
