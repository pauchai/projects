# Auth Bounded Context — Ubiquitous Language Glossary

This glossary defines the authoritative vocabulary for the **Identity & Access Management** bounded context. All code, documentation, API contracts, and team communication within this context MUST use these terms consistently.

**Bounded Context scope:** Authentication (verifying who you are), Authorization (determining what you can do), Session management, and Identity federation with external providers.

**Code mapping convention:**

- Python: `auth/domain/` for domain models, `auth/application/` for use cases, `auth/infrastructure/` for adapters


**Not to be confused with:** `CustomerId` in Billing or `RecipientId` in Shipping — those are separate identifiers within their own bounded contexts, linked to this Identity only through cross-context mapping.

---

### Principal

**Definition:** Any entity (user, service account, API key holder) that can be authenticated and authorized to perform actions. Principal is the abstract "actor" in the system.

**Context:** Used in authorization checks: "Does this principal have permission X on resource Y?" A Principal always resolves to an [Identity](#identity) but may be represented differently depending on the authentication method (user login, API key, service-to-service token).

**Code mapping:**

- Python: `Principal` Protocol in `auth/domain/principal.py`
 `Principal` interface in `auth/src/domain/principal.ts`

**Related terms:** [Identity](#identity), [Role](#role), [Claim](#claim)

---

### AuthUser

**Definition:** A human principal who authenticates via interactive methods (login form, SSO, biometric). Holds credentials, profile metadata, and assigned roles.

**Context:** The primary entity in the Auth context. Deliberately named `AuthUser` (not just `User`) to avoid collision with `User` entities in other bounded contexts (e.g., `BillingCustomer`, `ShippingRecipient`).

**Code mapping:**

- Python: `AuthUser` dataclass in `auth/domain/user.py`
 `AuthUser` class in `auth/src/domain/auth-user.ts`

**Related terms:** [Identity](#identity), [Credential](#credential), [Profile](#profile), [Role](#role)

**Not to be confused with:** `User` in other contexts. In Billing, the same person is a `Customer` (balance, subscriptions). In Shipping, they are a `Recipient` (address, contact info).

---

### Account

**Definition:** A container that groups one or more [AuthUsers](#authuser) under a single billing or organizational entity. In B2B systems, an Account typically represents a company or team.

**Context:** Used for tenant isolation, subscription management boundaries, and organizational-level access policies. An Account has its own set of [Roles](#role) and [Policies](#policy). In B2C systems without multi-tenancy, Account and AuthUser may be 1:1.

**Code mapping:**

- Python: `Account` dataclass in `auth/domain/account.py`
 `Account` class in `auth/src/domain/account.ts`

**Related terms:** [AuthUser](#authuser), [Role](#role), [Policy](#policy)

---

### Credential

**Definition:** A piece of evidence that proves the identity of a [Principal](#principal). Credentials are secret and must never be stored in plaintext or logged.

**Context:** A single AuthUser may have multiple credentials of different types: password hash, TOTP secret, WebAuthn public key, API key hash. Credentials are validated during [Authentication](#authentication) and rotated periodically.

**Code mapping:**

- Python: `Credential` Protocol in `auth/domain/credential.py` with implementations `PasswordCredential`, `TotpCredential`, `WebAuthnCredential`
 `Credential` interface in `auth/src/domain/credential.ts` with implementations `PasswordCredential`, `TotpCredential`, `WebAuthnCredential`

**Related terms:** [Authentication](#authentication), [Password Hash](#password-hash), [Passkey / WebAuthn](#passkey--webauthn)

---

### Profile

**Definition:** Non-security metadata associated with an [AuthUser](#authuser): display name, avatar URL, locale, timezone. Profile data has no impact on authentication or authorization decisions.

**Context:** Profile is the only part of AuthUser that can be freely shared with other bounded contexts via events or API without security concerns. Changes to profile do not trigger re-authentication.

**Code mapping:**

- Python: `UserProfile` dataclass in `auth/domain/profile.py`
 `UserProfile` type in `auth/src/domain/profile.ts`

**Related terms:** [AuthUser](#authuser)

**Not to be confused with:** Business-specific attributes like `shippingAddress` (Shipping context) or `paymentMethod` (Billing context).

---

## 2. Authentication

### Authentication

**Definition:** The process of verifying that a [Principal](#principal) is who they claim to be by validating one or more [Credentials](#credential).

**Context:** Authentication is a prerequisite for [Authorization](#authorization). The result of successful authentication is a [Session](#session) or [Token Pair](#token-pair). Authentication can be single-factor (password only) or multi-factor ([MFA](#multi-factor-authentication-mfa)).

**Code mapping:**

- Python: `AuthenticationService` in `auth/application/authentication_service.py`
 `AuthenticationService` in `auth/src/application/authentication-service.ts`

**Related terms:** [Credential](#credential), [Authentication Factor](#authentication-factor), [Session](#session), [Authorization](#authorization)

**Not to be confused with:** [Authorization](#authorization) — authentication answers "who are you?", authorization answers "what can you do?".

---

### Authentication Factor

**Definition:** A category of evidence used during authentication. The three standard categories are: something you **know** (password, PIN), something you **have** (phone, hardware key), something you **are** (fingerprint, face).

**Context:** Each factor type provides a different level of assurance. Combining factors from different categories constitutes [MFA](#multi-factor-authentication-mfa). Two passwords are NOT two-factor authentication — they are the same factor type.

**Related terms:** [Multi-Factor Authentication (MFA)](#multi-factor-authentication-mfa), [Credential](#credential)

---

### Multi-Factor Authentication (MFA)

**Definition:** An authentication scheme that requires the principal to present credentials from two or more distinct [Authentication Factor](#authentication-factor) categories before access is granted.

**Context:** MFA significantly reduces the risk of account compromise. Common combinations: password (know) + TOTP code (have), password (know) + fingerprint (are). MFA can be enforced at the [Account](#account) level via [Policy](#policy) or required for specific [Permissions](#permission).

**Code mapping:**

- Python: `MfaChallengeService` in `auth/application/mfa_challenge_service.py`
 `MfaChallengeService` in `auth/src/application/mfa-challenge-service.ts`

**Related terms:** [Authentication Factor](#authentication-factor), [One-Time Password (OTP)](#one-time-password-otp), [Passkey / WebAuthn](#passkey--webauthn), [Authentication Challenge](#authentication-challenge)

---

### Password Hash

**Definition:** A one-way cryptographic transformation of a plaintext password, stored in place of the password itself. Verification is performed by hashing the candidate password and comparing it to the stored hash.

**Context:** Passwords are NEVER stored or transmitted in plaintext. Use adaptive hashing algorithms (bcrypt, Argon2id, scrypt) that are intentionally slow to resist brute-force attacks. The hash includes a per-user salt. Password hashes are a type of [Credential](#credential).

**Code mapping:**

- Python: `PasswordHasher` Protocol in `auth/domain/password_hasher.py`, implemented by `Argon2PasswordHasher` in `auth/infrastructure/`
 `PasswordHasher` interface in `auth/src/domain/password-hasher.ts`, implemented by `Argon2PasswordHasher` in `auth/src/infrastructure/`

**Related terms:** [Credential](#credential), [Brute Force Protection](#brute-force-protection)

---

### One-Time Password (OTP)

**Definition:** A short-lived numeric code valid for a single authentication attempt. Generated either by a time-based algorithm (TOTP — RFC 6238) or sent to the user via SMS/email (HOTP or delivery-based OTP).

**Context:** OTP is a "something you have" [Authentication Factor](#authentication-factor) — it proves possession of a registered device or access to a delivery channel. TOTP is preferred over SMS-based OTP due to SIM-swap attack vectors. OTP codes typically expire within 30-60 seconds.

**Code mapping:**

- Python: `OtpVerifier` Protocol in `auth/domain/otp_verifier.py`
 `OtpVerifier` interface in `auth/src/domain/otp-verifier.ts`

**Related terms:** [Multi-Factor Authentication (MFA)](#multi-factor-authentication-mfa), [Authentication Challenge](#authentication-challenge)

---

### Passkey / WebAuthn

**Definition:** A passwordless authentication method based on the WebAuthn standard (FIDO2). The user authenticates using a device-bound cryptographic key pair, confirmed by a local gesture (biometric, PIN). The private key never leaves the user's device.

**Context:** Passkeys are the strongest form of "something you have" + "something you are" factor, providing phishing resistance. The server stores only the public key and a credential ID. Passkeys can replace both password and MFA in a single step.

**Code mapping:**

- Python: `WebAuthnCredential` dataclass in `auth/domain/credential.py`, `WebAuthnVerifier` in `auth/infrastructure/`
 `WebAuthnCredential` type in `auth/src/domain/credential.ts`, `WebAuthnVerifier` in `auth/src/infrastructure/`

**Related terms:** [Credential](#credential), [Authentication Factor](#authentication-factor), [Multi-Factor Authentication (MFA)](#multi-factor-authentication-mfa)

---

### Biometric Factor

**Definition:** An authentication factor based on a physical characteristic of the user: fingerprint, facial geometry, iris scan, voice pattern. Classified as "something you are."

**Context:** Biometrics are always processed **locally on the user's device** — the server never receives raw biometric data. The device confirms the biometric match and releases a cryptographic key (see [Passkey / WebAuthn](#passkey--webauthn)). Biometric templates are not [Credentials](#credential) from the server's perspective — the credential is the cryptographic key they unlock.

**Related terms:** [Authentication Factor](#authentication-factor), [Passkey / WebAuthn](#passkey--webauthn)

---

### Authentication Challenge

**Definition:** A server-initiated request asking the [Principal](#principal) to prove their identity by completing a specific step: entering a password, providing an OTP code, performing a biometric gesture, or approving a push notification.

**Context:** An authentication flow may consist of multiple sequential challenges (step-up authentication). Each challenge targets a specific [Authentication Factor](#authentication-factor). The challenge includes a cryptographic nonce to prevent replay attacks.

**Code mapping:**

- Python: `AuthChallenge` dataclass in `auth/domain/auth_challenge.py`
 `AuthChallenge` type in `auth/src/domain/auth-challenge.ts`

**Related terms:** [Authentication](#authentication), [Multi-Factor Authentication (MFA)](#multi-factor-authentication-mfa)

---

## 3. Sessions & Tokens

### Session

**Definition:** A stateful, time-bounded record that represents an authenticated [Principal](#principal)'s active interaction with the system. A Session is created upon successful [Authentication](#authentication) and destroyed on logout or expiry.

**Context:** Sessions are the primary mechanism for maintaining authenticated state across HTTP requests. Each session is bound to a single [Identity](#identity), tracks creation time, last activity, IP address, and user agent. Sessions can be explicitly revoked (logout) or expire after inactivity (idle timeout) or absolute duration (max lifetime).

**Code mapping:**

- Python: `Session` dataclass in `auth/domain/session.py`, `SessionRepository` Protocol in `auth/domain/session_repository.py`
 `Session` class in `auth/src/domain/session.ts`, `SessionRepository` interface in `auth/src/domain/session-repository.ts`

**Related terms:** [Access Token](#access-token), [Token Pair](#token-pair), [Token Expiry (TTL)](#token-expiry-ttl)

---

### Access Token

**Definition:** A short-lived, self-contained token (typically a [JWT](#jwt-json-web-token)) that proves the bearer's identity and carries authorization metadata ([Claims](#claim), [Scopes](#scope)). Presented with each API request.

**Context:** Access tokens are stateless — the server validates them by checking the cryptographic signature and expiry without hitting a database. Short TTL (5-15 minutes) limits the window of abuse if a token is compromised. When the access token expires, the client uses a [Refresh Token](#refresh-token) to obtain a new one.

**Code mapping:**

- Python: `AccessToken` dataclass in `auth/domain/token.py`, `TokenIssuer` Protocol in `auth/domain/token_issuer.py`
 `AccessToken` type in `auth/src/domain/token.ts`, `TokenIssuer` interface in `auth/src/domain/token-issuer.ts`

**Related terms:** [Refresh Token](#refresh-token), [Token Pair](#token-pair), [JWT (JSON Web Token)](#jwt-json-web-token), [Claim](#claim), [Scope](#scope)

---

### Refresh Token

**Definition:** A long-lived, opaque token used exclusively to obtain new [Access Tokens](#access-token) without requiring the user to re-authenticate. Stored securely on the client side (httpOnly cookie or secure storage).

**Context:** Refresh tokens are stateful — the server tracks them in a database and can revoke them individually. They are single-use: each refresh operation issues a new refresh token and invalidates the previous one (rotation). If a refresh token is reused, it indicates theft — the server MUST revoke the entire [Session](#session).

**Code mapping:**

- Python: `RefreshToken` dataclass in `auth/domain/token.py`, stored via `RefreshTokenRepository` Protocol
 `RefreshToken` type in `auth/src/domain/token.ts`, stored via `RefreshTokenRepository` interface

**Related terms:** [Access Token](#access-token), [Token Pair](#token-pair), [Token Revocation](#token-revocation), [Session](#session)

---

### Token Pair

**Definition:** The combination of an [Access Token](#access-token) and a [Refresh Token](#refresh-token) issued together upon successful [Authentication](#authentication). The pair represents a complete set of credentials for API access.

**Context:** Issued at the end of the authentication flow. The access token is used for every request; the refresh token is used only when the access token expires. Both tokens are bound to the same [Session](#session) and [Identity](#identity).

**Code mapping:**

- Python: `TokenPair` dataclass in `auth/domain/token.py`
 `TokenPair` type in `auth/src/domain/token.ts`

**Related terms:** [Access Token](#access-token), [Refresh Token](#refresh-token), [Session](#session)

---

### Token Revocation

**Definition:** The act of explicitly invalidating a token before its natural expiry. Revoked tokens MUST be rejected on subsequent use.

**Context:** Revocation is essential for logout, password change, permission change, and compromised-token scenarios. Access tokens (stateless JWTs) are difficult to revoke individually — common strategies include short TTL + refresh token revocation, or maintaining a revocation list / blocklist for critical cases. Refresh tokens are always revocable because they are stored server-side.

**Code mapping:**

- Python: `TokenRevocationService` in `auth/application/token_revocation_service.py`
 `TokenRevocationService` in `auth/src/application/token-revocation-service.ts`

**Related terms:** [Access Token](#access-token), [Refresh Token](#refresh-token), [Session](#session)

---

### Token Expiry (TTL)

**Definition:** The duration after which a token becomes invalid. TTL (Time To Live) is set at issuance and cannot be extended — a new token must be issued.

**Context:** Recommended TTLs: Access Token — 5-15 minutes. Refresh Token — 7-30 days. Session idle timeout — 30-60 minutes. Session absolute timeout — 8-24 hours. Shorter TTLs increase security but reduce convenience. TTL values should be configurable via [Policy](#policy).

**Related terms:** [Access Token](#access-token), [Refresh Token](#refresh-token), [Session](#session), [Policy](#policy)

---

### JWT (JSON Web Token)

**Definition:** A compact, URL-safe token format (RFC 7519) consisting of three Base64-encoded parts: header (algorithm), payload ([Claims](#claim)), and signature. The signature ensures the token has not been tampered with.

**Context:** JWT is the standard format for [Access Tokens](#access-token) in this context. The payload carries identity and authorization [Claims](#claim). JWTs are signed (JWS) but not encrypted by default — do not place secrets in the payload. Use RS256 or ES256 algorithms for asymmetric verification (allows resource servers to validate tokens without the signing key).

**Related terms:** [Access Token](#access-token), [Claim](#claim)

**Not to be confused with:** JWT is a token format, not an authentication protocol. OAuth 2.0 and OIDC are protocols that may use JWTs as a token format.

---

## 4. Authorization & Access Control

### Authorization

**Definition:** The process of determining whether an authenticated [Principal](#principal) is permitted to perform a specific action on a specific resource.

**Context:** Authorization happens AFTER [Authentication](#authentication). It evaluates the principal's [Roles](#role), [Permissions](#permission), [Claims](#claim), and applicable [Policies](#policy). Authorization decisions can be enforced at multiple layers: API gateway, application service, domain entity.

**Code mapping:**

- Python: `AuthorizationService` in `auth/application/authorization_service.py`
 `AuthorizationService` in `auth/src/application/authorization-service.ts`

**Related terms:** [Authentication](#authentication), [Permission](#permission), [Role](#role), [Policy](#policy)

---

### Permission

**Definition:** A granular, atomic right to perform a single action on a single resource type. Permissions are the smallest unit of access control.

**Context:** Permissions follow the format `resource:action` (e.g., `order:create`, `user:delete`, `report:export`). Permissions are assigned to [Roles](#role), not directly to users. A principal's effective permissions are the union of all permissions from all their assigned roles.

**Code mapping:**

- Python: `Permission` value object in `auth/domain/permission.py`
 `Permission` branded type in `auth/src/domain/permission.ts`

**Related terms:** [Role](#role), [Authorization](#authorization), [Scope](#scope)

---

### Role

**Definition:** A named collection of [Permissions](#permission) that represents a job function or responsibility level. Roles are assigned to [AuthUsers](#authuser) within the scope of an [Account](#account).

**Context:** Roles simplify permission management: instead of assigning 50 permissions to each user, assign one role. Roles should be named after business functions (`order_manager`, `billing_admin`, `read_only_auditor`), not technical levels (`admin`, `superuser`). Avoid hierarchical role inheritance — prefer flat, composable roles.

**Code mapping:**

- Python: `Role` dataclass in `auth/domain/role.py`
 `Role` class in `auth/src/domain/role.ts`

**Related terms:** [Permission](#permission), [RBAC (Role-Based Access Control)](#rbac-role-based-access-control), [AuthUser](#authuser)

---

### RBAC (Role-Based Access Control)

**Definition:** An authorization model where access decisions are based on the [Roles](#role) assigned to the [Principal](#principal). The principal's effective permissions are determined by the union of all permissions associated with their roles.

**Context:** RBAC is the default authorization model for most applications. It works well when access rules are stable and role-based. For dynamic, attribute-based rules (e.g., "users can only edit their own orders"), combine RBAC with [ABAC](#abac-attribute-based-access-control) or domain-level checks.

**Related terms:** [Role](#role), [Permission](#permission), [ABAC (Attribute-Based Access Control)](#abac-attribute-based-access-control)

---

### ABAC (Attribute-Based Access Control)

**Definition:** An authorization model where access decisions are based on attributes of the principal, the resource, the action, and the environment (time, IP, location). Policies are expressed as rules over these attributes.

**Context:** ABAC is more flexible than [RBAC](#rbac-role-based-access-control) but more complex to implement and audit. Use ABAC when access rules depend on dynamic conditions: "managers can approve expenses under $10,000", "users can access documents in their department only during business hours". In practice, RBAC and ABAC are often combined.

**Code mapping:**

- Python: `AttributePolicy` in `auth/domain/policy.py`
 `AttributePolicy` in `auth/src/domain/policy.ts`

**Related terms:** [RBAC (Role-Based Access Control)](#rbac-role-based-access-control), [Policy](#policy), [Claim](#claim)

---

### Policy

**Definition:** A declarative rule that governs authentication and authorization behavior. Policies define requirements (e.g., "MFA required for admin roles"), restrictions (e.g., "max 5 login attempts per minute"), and access rules (e.g., "read-only access from untrusted networks").

**Context:** Policies are evaluated by the [AuthorizationService](#authorization) and [AuthenticationService](#authentication). They can be scoped to an [Account](#account), a [Role](#role), or a specific resource. Policies are the primary mechanism for enforcing security requirements without hardcoding them in business logic.

**Code mapping:**

- Python: `Policy` Protocol in `auth/domain/policy.py`, `PolicyEvaluator` in `auth/application/policy_evaluator.py`
 `Policy` interface in `auth/src/domain/policy.ts`, `PolicyEvaluator` in `auth/src/application/policy-evaluator.ts`

**Related terms:** [ABAC (Attribute-Based Access Control)](#abac-attribute-based-access-control), [Multi-Factor Authentication (MFA)](#multi-factor-authentication-mfa), [Account Lockout](#account-lockout)

---

### Scope

**Definition:** A named boundary that limits the access granted by an [Access Token](#access-token). Scopes define what subset of the API the token holder can access, regardless of the user's full set of [Permissions](#permission).

**Context:** Scopes are primarily used in [OAuth 2.0](#oauth-20) flows. A client application requests specific scopes (e.g., `read:profile`, `write:orders`), and the user consents. The issued token is restricted to those scopes even if the user has broader permissions. Scopes are coarser-grained than permissions.

**Related terms:** [Access Token](#access-token), [Permission](#permission), [OAuth 2.0](#oauth-20), [Claim](#claim)

---

### Claim

**Definition:** A key-value pair embedded in a [JWT](#jwt-json-web-token) that asserts a fact about the [Principal](#principal). Standard claims include `sub` (subject/identity), `iss` (issuer), `exp` (expiry), `aud` (audience). Custom claims carry domain-specific data: `roles`, `account_id`, `permissions`.

**Context:** Claims are the primary vehicle for transmitting identity and authorization data in a stateless manner. Resource servers extract claims from the access token to make authorization decisions without querying the auth service. Keep claims minimal — large tokens increase bandwidth and parsing overhead.

**Related terms:** [JWT (JSON Web Token)](#jwt-json-web-token), [Access Token](#access-token), [Scope](#scope), [Role](#role)

---

### ACL (Access Control List)

**Definition:** A per-resource list that specifies which [Principals](#principal) (or [Roles](#role)) have which [Permissions](#permission) on that specific resource instance.

**Context:** ACLs provide fine-grained, instance-level access control: "User A can edit Document X, User B can only view it." Use ACLs when access rules vary per resource instance. ACLs are complementary to [RBAC](#rbac-role-based-access-control) (role-level) and [ABAC](#abac-attribute-based-access-control) (attribute-level). Storing and evaluating ACLs can be expensive at scale — consider caching or denormalizing.

**Code mapping:**

- Python: `AccessControlList` in `auth/domain/acl.py`
 `AccessControlList` in `auth/src/domain/acl.ts`

**Related terms:** [Permission](#permission), [Principal](#principal), [RBAC (Role-Based Access Control)](#rbac-role-based-access-control)

---

### Privilege Escalation

**Definition:** The act of a [Principal](#principal) gaining permissions beyond what they were originally granted. Can be legitimate (step-up authentication for sensitive operations) or malicious (exploiting a vulnerability to gain admin access).

**Context:** The system MUST protect against unauthorized privilege escalation: users cannot assign themselves roles, modify their own permissions, or create tokens with elevated claims. Legitimate escalation (sudo-like step-up) requires re-authentication with a stronger factor. All escalation events MUST be recorded in the [Audit Log](#audit-log).

**Related terms:** [Authorization](#authorization), [Multi-Factor Authentication (MFA)](#multi-factor-authentication-mfa), [Audit Log](#audit-log), [Security Event](#security-event)

---

## 5. Federation & External Identity

### Identity Provider (IdP)

**Definition:** An external service that authenticates users and issues identity assertions (tokens, SAML assertions) that your system trusts. The IdP is the authoritative source of identity for federated users.

**Context:** Examples: Google, Okta, Azure AD, Auth0. When using an IdP, your system does not manage passwords or MFA for federated users — the IdP handles that. Your system receives an identity assertion, validates it, and maps the external identity to a local [AuthUser](#authuser) (provisioning). The adapter that communicates with the IdP is an [Anti-Corruption Layer](../AGENTS.md#43-context-mapping-карта-контекстов).

**Code mapping:**

- Python: `IdentityProviderGateway` Protocol in `auth/domain/identity_provider_gateway.py`
 `IdentityProviderGateway` interface in `auth/src/domain/identity-provider-gateway.ts`

**Related terms:** [Service Provider (SP)](#service-provider-sp), [Federation](#federation), [SSO (Single Sign-On)](#sso-single-sign-on)

---

### Service Provider (SP)

**Definition:** Your application in the context of federation — the system that relies on an [Identity Provider (IdP)](#identity-provider-idp) to authenticate users and consumes identity assertions.

**Context:** As a Service Provider, your system: (1) redirects unauthenticated users to the IdP, (2) receives and validates identity assertions (OAuth tokens, SAML responses), (3) creates or updates a local [Session](#session) based on the validated assertion.

**Related terms:** [Identity Provider (IdP)](#identity-provider-idp), [OAuth 2.0](#oauth-20), [SAML](#saml)

---

### OAuth 2.0

**Definition:** An authorization framework (RFC 6749) that enables third-party applications to obtain limited access to a user's resources without exposing the user's [Credentials](#credential). OAuth 2.0 defines grant types (authorization code, client credentials, etc.) for different scenarios.

**Context:** OAuth 2.0 is NOT an authentication protocol — it handles authorization (delegated access). For authentication, use [OpenID Connect (OIDC)](#openid-connect-oidc) which is built on top of OAuth 2.0. The Authorization Code flow with PKCE is the recommended grant type for web and mobile applications.

**Related terms:** [OpenID Connect (OIDC)](#openid-connect-oidc), [Scope](#scope), [Access Token](#access-token), [Refresh Token](#refresh-token)

**Not to be confused with:** Authentication. OAuth 2.0 alone does not verify identity — it only delegates access. Use OIDC for identity verification.

---

### OpenID Connect (OIDC)

**Definition:** An identity layer built on top of [OAuth 2.0](#oauth-20) that adds authentication. OIDC introduces the ID Token (a [JWT](#jwt-json-web-token) containing identity [Claims](#claim)) and a standardized UserInfo endpoint.

**Context:** OIDC is the recommended protocol for "Login with Google/GitHub/Azure" flows. The ID Token contains standard claims (`sub`, `email`, `name`) that identify the user. Your system validates the ID Token signature and maps the external identity to a local [AuthUser](#authuser).

**Code mapping:**

- Python: `OidcProviderAdapter` in `auth/infrastructure/oidc_provider_adapter.py`
 `OidcProviderAdapter` in `auth/src/infrastructure/oidc-provider-adapter.ts`

**Related terms:** [OAuth 2.0](#oauth-20), [Identity Provider (IdP)](#identity-provider-idp), [JWT (JSON Web Token)](#jwt-json-web-token), [Claim](#claim)

---

### SAML

**Definition:** Security Assertion Markup Language — an XML-based standard for exchanging authentication and authorization data between an [Identity Provider (IdP)](#identity-provider-idp) and a [Service Provider (SP)](#service-provider-sp).

**Context:** SAML is common in enterprise environments (Active Directory Federation Services, Okta). The IdP issues a signed XML assertion containing the user's identity and attributes. Your system validates the signature, extracts identity data, and creates a local [Session](#session). SAML is being gradually replaced by [OIDC](#openid-connect-oidc) but remains dominant in legacy enterprise integrations.

**Code mapping:**

- Python: `SamlProviderAdapter` in `auth/infrastructure/saml_provider_adapter.py`
 `SamlProviderAdapter` in `auth/src/infrastructure/saml-provider-adapter.ts`

**Related terms:** [Identity Provider (IdP)](#identity-provider-idp), [Service Provider (SP)](#service-provider-sp), [Federation](#federation)

---

### Federation

**Definition:** The practice of trusting an external [Identity Provider (IdP)](#identity-provider-idp) to authenticate users on your behalf. Federated identity allows users to use a single set of credentials across multiple independent systems.

**Context:** Federation introduces a trust boundary: your system trusts the IdP to correctly authenticate the user, but you still make your own [Authorization](#authorization) decisions. Federated users need to be mapped (provisioned) to local [AuthUsers](#authuser) — either on first login (JIT provisioning) or via directory sync (SCIM). Federation adapters are Anti-Corruption Layers (see [AGENTS.md 4.3](../AGENTS.md#43-context-mapping-карта-контекстов)).

**Related terms:** [Identity Provider (IdP)](#identity-provider-idp), [SSO (Single Sign-On)](#sso-single-sign-on), [OAuth 2.0](#oauth-20), [OIDC](#openid-connect-oidc), [SAML](#saml)

---

### SSO (Single Sign-On)

**Definition:** A user experience where a single [Authentication](#authentication) event grants access to multiple independent applications without re-entering credentials.

**Context:** SSO is implemented via [Federation](#federation): all applications trust the same [Identity Provider (IdP)](#identity-provider-idp). When the user logs into one application, the IdP establishes a session. Subsequent applications detect the existing IdP session and skip the login step. SSO improves UX but increases the blast radius of a compromised IdP session.

**Related terms:** [Federation](#federation), [Identity Provider (IdP)](#identity-provider-idp), [Session](#session)

---

### Social Login

**Definition:** A form of [Federation](#federation) where the [Identity Provider (IdP)](#identity-provider-idp) is a consumer-facing social platform: Google, GitHub, Apple, Facebook.

**Context:** Social Login reduces friction for B2C applications by eliminating registration forms. It uses [OIDC](#openid-connect-oidc) or [OAuth 2.0](#oauth-20) under the hood. On first login, the system provisions a new [AuthUser](#authuser) from the provider's profile data. Users may link multiple social providers to a single [Identity](#identity).

**Related terms:** [Federation](#federation), [OpenID Connect (OIDC)](#openid-connect-oidc), [Identity Provider (IdP)](#identity-provider-idp)

---

## 6. Security Events & Audit

### Login Attempt

**Definition:** A single, recorded instance of a [Principal](#principal) trying to authenticate. Every attempt is logged regardless of outcome: success, failure (wrong password), blocked (account locked), or challenged (MFA required).

**Context:** Login attempts are the primary input for [Brute Force Protection](#brute-force-protection) and [Audit Log](#audit-log). Each attempt records: timestamp, identity (if known), IP address, user agent, authentication method, and result. Failed attempts increment the lockout counter.

**Code mapping:**

- Python: `LoginAttempt` dataclass in `auth/domain/login_attempt.py`
 `LoginAttempt` type in `auth/src/domain/login-attempt.ts`

**Related terms:** [Authentication](#authentication), [Brute Force Protection](#brute-force-protection), [Account Lockout](#account-lockout), [Audit Log](#audit-log)

---

### Brute Force Protection

**Definition:** A defense mechanism that limits the rate and number of failed [Login Attempts](#login-attempt) to prevent credential guessing attacks.

**Context:** Implemented via progressive delays, CAPTCHA challenges, and [Account Lockout](#account-lockout). Strategies include: per-IP rate limiting, per-account attempt counting, and global anomaly detection. Brute force protection MUST NOT reveal whether an account exists (use generic error messages like "Invalid credentials").

**Code mapping:**

- Python: `BruteForceProtectionService` in `auth/application/brute_force_protection_service.py`
 `BruteForceProtectionService` in `auth/src/application/brute-force-protection-service.ts`

**Related terms:** [Login Attempt](#login-attempt), [Account Lockout](#account-lockout), [Policy](#policy)

---

### Account Lockout

**Definition:** A temporary or permanent restriction on an [Account](#account) or [AuthUser](#authuser) that prevents further [Authentication](#authentication) after a threshold of failed [Login Attempts](#login-attempt) is reached.

**Context:** Lockout duration and threshold are defined by [Policy](#policy) (e.g., "lock after 5 failures for 15 minutes"). Lockout MUST be per-account, not per-IP (to prevent distributed attacks from bypassing per-IP limits). Administrators can manually unlock accounts. All lockout events are recorded as [Security Events](#security-event).

**Code mapping:**

- Python: `AccountLockoutPolicy` in `auth/domain/policy.py`
 `AccountLockoutPolicy` in `auth/src/domain/policy.ts`

**Related terms:** [Brute Force Protection](#brute-force-protection), [Login Attempt](#login-attempt), [Policy](#policy), [Security Event](#security-event)

---

### Audit Log

**Definition:** An append-only, tamper-resistant record of all security-relevant actions within the Auth context. Every authentication, authorization decision, permission change, session creation/destruction, and policy modification MUST be logged.

**Context:** The audit log is the foundation for security investigations, compliance reporting (SOC 2, GDPR, HIPAA), and anomaly detection. Entries are immutable — they can be read and archived, but never modified or deleted. Each entry includes: timestamp, actor ([Identity](#identity)), action, target resource, result (success/failure), and metadata (IP, user agent).

**Code mapping:**

- Python: `AuditLogger` Protocol in `auth/domain/audit_logger.py`, implemented in `auth/infrastructure/`
 `AuditLogger` interface in `auth/src/domain/audit-logger.ts`, implemented in `auth/src/infrastructure/`

**Related terms:** [Security Event](#security-event), [Login Attempt](#login-attempt)

---

### Security Event

**Definition:** A domain event emitted when a security-relevant action occurs within the Auth context. Security events are consumed by the [Audit Log](#audit-log), monitoring systems, and potentially other bounded contexts.

**Context:** Examples: `UserAuthenticated`, `AuthenticationFailed`, `SessionRevoked`, `RoleAssigned`, `PermissionDenied`, `AccountLocked`, `PasswordChanged`, `MfaEnabled`. Security events follow the Published Language pattern (see [AGENTS.md 4.3](../AGENTS.md#43-context-mapping-карта-контекстов)) — they are the official contract for external consumers.

**Code mapping:**

- Python: `SecurityEvent` base dataclass in `auth/domain/events.py` with specific subclasses (`UserAuthenticatedEvent`, `AuthenticationFailedEvent`, etc.)
 `SecurityEvent` union type in `auth/src/domain/events.ts` with specific types (`UserAuthenticatedEvent`, `AuthenticationFailedEvent`, etc.)

**Related terms:** [Audit Log](#audit-log), [Login Attempt](#login-attempt), [Privilege Escalation](#privilege-escalation)

---

## Cross-Context Boundary Notes

The Auth bounded context interacts with other contexts through explicit contracts. The following table clarifies term boundaries:

| Auth Context Term | Other Context | Their Term | Relationship |
|-------------------|---------------|------------|--------------|
| `AuthUser` | Billing | [`Billing Customer`](./billing.md#billing-customer) | Linked via `IdentityId`. Auth owns login/roles; Billing owns balance/subscriptions. |
| `AuthUser` | Shipping | `Recipient` | Linked via `IdentityId`. Auth owns credentials; Shipping owns address/delivery preferences. |
| `AuthUser` | Partnership | [`Partner`](./partnership.md#partner) | Linked via `IdentityId`. Auth owns credentials, sessions, and roles; Partnership owns referral relationships and commissions. |
| `AuthUser` | Project | [`Member`](./project.md#member) | Linked via `IdentityId`. Auth owns credentials, sessions, and system-wide roles; Project owns project-scoped membership and project-scoped roles. |
| `AuthUser` | Learning | [`Master`](./learning.md#master) | Linked via `IdentityId`. Auth owns credentials and sessions; Learning owns specialization, verification status, teaching profile, and capacity. |
| `AuthUser` | Learning | [`Learner`](./learning.md#learner) | Linked via `IdentityId`. Auth owns credentials and sessions; Learning owns learner status, progress, and mentorship data. |
| `Account` | Billing | [`Billing Account`](./billing.md#billing-account) | May share the same ID. Auth owns access policies; Billing owns payment methods/invoices. |
| `Permission` | Project | [`Project Permission`](./project.md#project-permission) | Auth provides system-wide RBAC (e.g., "can create projects"). Project defines and enforces project-scoped permissions (e.g., `edit_content`, `manage_members`). They are complementary, not overlapping. |
| `Role` | Project | [`Owner`](./project.md#owner), [`Member Role`](./project.md#member-role), [`Viewer Role`](./project.md#viewer-role) | Auth defines system-wide roles (e.g., Admin). Project defines project-scoped roles (Owner, Member, Viewer). An Auth Admin has platform-wide privileges; a Project Owner only has control within their specific project. |
| `Identity` verification | Learning | [`Master Verification`](./learning.md#master-verification) | Auth may verify identity documents (passport, ID). Learning independently verifies professional credentials (licenses, certifications, work experience). The two verifications are complementary, not overlapping. |
| `Permission` | Domain services | Domain-specific checks | Auth provides coarse-grained RBAC; domain services enforce fine-grained business rules. |
| `SecurityEvent` | Partnership | [`Referral Fraud`](./partnership.md#referral-fraud) | Fraud detection in Partnership emits events that Auth/Security may consume for cross-context threat analysis. |
| `SecurityEvent` | Monitoring | `Alert` | Auth emits events; Monitoring context consumes and correlates them into alerts. |

**Integration rules:**

- Other contexts MUST NOT import Auth domain models directly. Use events or API contracts.
- Auth MUST NOT contain business logic from other contexts (e.g., "users with unpaid invoices cannot log in" — this rule belongs in Billing, enforced via a policy callback or event).
- When another context needs identity data, Auth publishes it via `SecurityEvent` or a dedicated read API — never by sharing database tables.
