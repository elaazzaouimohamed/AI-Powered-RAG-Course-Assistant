package com.rag.app.service;

import com.rag.app.dto.auth.*;
import com.rag.app.model.User;
import com.rag.app.repository.UserRepository;
import com.rag.app.security.JwtTokenProvider;
import com.rag.app.security.LoginAttemptService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.*;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final AuthenticationManager authManager;
    private final JwtTokenProvider tokenProvider;
    private final UserRepository userRepo;
    private final PasswordEncoder encoder;
    private final UserDetailsService userDetailsService;
    private final LoginAttemptService loginAttemptService;

    public AuthResponse login(LoginRequest req) {
        String key = req.getUsername();

        // Anti brute-force : bloque temporairement après plusieurs échecs consécutifs,
        // avant même de toucher la base ou le hachage du mot de passe.
        if (loginAttemptService.isBlocked(key)) {
            long mins = Math.max(1, loginAttemptService.secondsUntilUnlocked(key) / 60 + 1);
            throw new LockedException("Trop de tentatives échouées. Réessayez dans " + mins + " min.");
        }

        Authentication auth;
        try {
            auth = authManager.authenticate(
                    new UsernamePasswordAuthenticationToken(req.getUsername(), req.getPassword()));
        } catch (BadCredentialsException e) {
            loginAttemptService.loginFailed(key);
            throw e;
        }
        loginAttemptService.loginSucceeded(key);

        User user = userRepo.findByUsername(req.getUsername()).orElseThrow();
        String access  = tokenProvider.generateAccessToken(auth);
        String refresh = tokenProvider.generateRefreshToken(user.getUsername());

        return AuthResponse.builder()
                .accessToken(access)
                .refreshToken(refresh)
                .username(user.getUsername())
                .email(user.getEmail())
                .role(user.getRole().name())
                .build();
    }

    public AuthResponse register(RegisterRequest req) {
        if (userRepo.existsByUsername(req.getUsername()))
            throw new IllegalArgumentException("Username already taken");
        if (userRepo.existsByEmail(req.getEmail()))
            throw new IllegalArgumentException("Email already registered");

        User user = userRepo.save(User.builder()
                .username(req.getUsername())
                .email(req.getEmail())
                .password(encoder.encode(req.getPassword()))
                .build());

        Authentication auth = authManager.authenticate(
                new UsernamePasswordAuthenticationToken(req.getUsername(), req.getPassword()));

        return AuthResponse.builder()
                .accessToken(tokenProvider.generateAccessToken(auth))
                .refreshToken(tokenProvider.generateRefreshToken(user.getUsername()))
                .username(user.getUsername())
                .email(user.getEmail())
                .role(user.getRole().name())
                .build();
    }

    public AuthResponse me(String username) {
        User user = userRepo.findByUsername(username)
                .orElseThrow(() -> new IllegalArgumentException("Utilisateur introuvable"));
        return AuthResponse.builder()
                .username(user.getUsername())
                .email(user.getEmail())
                .role(user.getRole().name())
                .build();
    }

    public void changePassword(String username, String currentPassword, String newPassword) {
        if (newPassword == null || newPassword.length() < 6)
            throw new IllegalArgumentException("Le nouveau mot de passe doit faire au moins 6 caractères.");
        User user = userRepo.findByUsername(username)
                .orElseThrow(() -> new IllegalArgumentException("Utilisateur introuvable"));
        if (!encoder.matches(currentPassword, user.getPassword()))
            throw new IllegalArgumentException("Mot de passe actuel incorrect.");
        user.setPassword(encoder.encode(newPassword));
        userRepo.save(user);
    }

    public AuthResponse refresh(String refreshToken) {
        if (!tokenProvider.validateToken(refreshToken))
            throw new IllegalArgumentException("Invalid refresh token");

        String username = tokenProvider.getUsernameFromToken(refreshToken);
        User user = userRepo.findByUsername(username).orElseThrow();

        var userDetails = userDetailsService.loadUserByUsername(username);
        Authentication auth = new UsernamePasswordAuthenticationToken(
                userDetails, null, userDetails.getAuthorities());

        return AuthResponse.builder()
                .accessToken(tokenProvider.generateAccessToken(auth))
                .refreshToken(tokenProvider.generateRefreshToken(username))
                .username(user.getUsername())
                .email(user.getEmail())
                .role(user.getRole().name())
                .build();
    }
}
