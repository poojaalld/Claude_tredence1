package com.tredence.digitalbanking.accounts;

import com.tredence.digitalbanking.accounts.dto.AccountResponse;
import com.tredence.digitalbanking.accounts.dto.CreateAccountRequest;
import com.tredence.digitalbanking.auth.User;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/accounts")
@RequiredArgsConstructor
public class AccountController {

    private final AccountService accountService;

    @PostMapping
    public ResponseEntity<AccountResponse> createAccount(@AuthenticationPrincipal User owner,
                                                           @Valid @RequestBody CreateAccountRequest request) {
        Account account = accountService.createAccount(owner, request.accountType());
        return ResponseEntity.ok(AccountResponse.from(account));
    }

    @GetMapping
    public ResponseEntity<List<AccountResponse>> listMyAccounts(@AuthenticationPrincipal User owner) {
        List<AccountResponse> accounts = accountService.getAccountsForOwner(owner.getId()).stream()
                .map(AccountResponse::from)
                .toList();
        return ResponseEntity.ok(accounts);
    }

    @GetMapping("/{accountNumber}")
    public ResponseEntity<AccountResponse> getAccount(@PathVariable String accountNumber) {
        return ResponseEntity.ok(AccountResponse.from(accountService.getByAccountNumber(accountNumber)));
    }
}
