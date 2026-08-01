package com.tredence.digitalbanking.accounts;

import com.tredence.digitalbanking.auth.User;
import com.tredence.digitalbanking.common.exception.BadRequestException;
import com.tredence.digitalbanking.common.exception.ResourceNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class AccountService {

    private final AccountRepository accountRepository;

    @Transactional
    public Account createAccount(User owner, AccountType accountType) {
        Account account = Account.builder()
                .accountNumber(generateAccountNumber())
                .owner(owner)
                .accountType(accountType)
                .balance(BigDecimal.ZERO)
                .createdAt(Instant.now())
                .build();
        return accountRepository.save(account);
    }

    public List<Account> getAccountsForOwner(Long ownerId) {
        return accountRepository.findByOwnerId(ownerId);
    }

    public Account getByAccountNumber(String accountNumber) {
        return accountRepository.findByAccountNumber(accountNumber)
                .orElseThrow(() -> new ResourceNotFoundException("No account found with number " + accountNumber));
    }

    @Transactional
    public void credit(Account account, BigDecimal amount) {
        account.setBalance(account.getBalance().add(amount));
        accountRepository.save(account);
    }

    @Transactional
    public void debit(Account account, BigDecimal amount) {
        if (account.getBalance().compareTo(amount) < 0) {
            throw new BadRequestException("Insufficient funds in account " + account.getAccountNumber());
        }
        account.setBalance(account.getBalance().subtract(amount));
        accountRepository.save(account);
    }

    private String generateAccountNumber() {
        String candidate;
        do {
            candidate = UUID.randomUUID().toString().replace("-", "").substring(0, 12).toUpperCase();
        } while (accountRepository.existsByAccountNumber(candidate));
        return candidate;
    }
}
