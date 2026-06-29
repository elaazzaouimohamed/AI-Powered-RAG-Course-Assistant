package com.rag.app.security;

import org.junit.jupiter.api.Test;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.User;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

/** Tests unitaires du fournisseur de jetons JWT (signature, validation, expiration, falsification). */
class JwtTokenProviderTest {

    private static final String SECRET =
            "TestSecretKeyForJUnitRagExplicateurCours2025MinimumLength256bitsAAAA";
    private static final long ONE_HOUR = 3_600_000L;

    private JwtTokenProvider provider(long accessTtl) {
        return new JwtTokenProvider(SECRET, accessTtl, ONE_HOUR);
    }

    private Authentication auth(String username) {
        var userDetails = new User(username, "pwd",
                List.of(new SimpleGrantedAuthority("ROLE_USER")));
        return new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());
    }

    @Test
    void generatesAndValidatesAToken() {
        var p = provider(ONE_HOUR);
        String token = p.generateAccessToken(auth("alice"));

        assertThat(p.validateToken(token)).isTrue();
        assertThat(p.getUsernameFromToken(token)).isEqualTo("alice");
    }

    @Test
    void rejectsATamperedToken() {
        var p = provider(ONE_HOUR);
        String token = p.generateAccessToken(auth("bob"));
        String tampered = token.substring(0, token.length() - 2) + "xx";

        assertThat(p.validateToken(tampered)).isFalse();
    }

    @Test
    void rejectsATokenSignedWithAnotherKey() {
        var issuer = new JwtTokenProvider(
                "CompletelyDifferentSecretKeyThatIsAlsoAtLeast256bitsLongForHS512xx",
                ONE_HOUR, ONE_HOUR);
        var verifier = provider(ONE_HOUR);

        String foreignToken = issuer.generateAccessToken(auth("eve"));

        assertThat(verifier.validateToken(foreignToken)).isFalse();
    }

    @Test
    void rejectsAnExpiredTokenBeyondClockSkew() {
        // TTL négatif de 60s : le jeton est déjà expiré, au-delà des 30s de tolérance d'horloge.
        var p = provider(-60_000L);
        String expired = p.generateAccessToken(auth("carol"));

        assertThat(p.validateToken(expired)).isFalse();
    }

    @Test
    void rejectsGarbageInput() {
        var p = provider(ONE_HOUR);
        assertThat(p.validateToken("not.a.jwt")).isFalse();
        assertThat(p.validateToken("")).isFalse();
    }
}
