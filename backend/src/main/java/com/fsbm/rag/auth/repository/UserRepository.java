package com.fsbm.rag.auth.repository;

import com.fsbm.rag.auth.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/**
 * Accès aux données des utilisateurs.
 */
@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    /**
     * Recherche un utilisateur par son adresse e-mail.
     *
     * @param email adresse e-mail (identifiant de connexion)
     * @return l'utilisateur correspondant, ou vide si inexistant
     */
    Optional<User> findByEmail(String email);

    /**
     * Vérifie l'existence d'un compte pour cet e-mail (évite de charger l'entité entière).
     *
     * @param email adresse e-mail à vérifier
     * @return {@code true} si un compte existe déjà
     */
    boolean existsByEmail(String email);
}
