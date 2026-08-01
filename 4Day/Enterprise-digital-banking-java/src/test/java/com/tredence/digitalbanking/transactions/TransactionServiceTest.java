package com.tredence.digitalbanking.transactions;

import com.tredence.digitalbanking.accounts.Account;
import com.tredence.digitalbanking.accounts.AccountService;
import com.tredence.digitalbanking.accounts.AccountType;
import com.tredence.digitalbanking.auth.Role;
import com.tredence.digitalbanking.auth.User;
import com.tredence.digitalbanking.auth.UserRepository;
import com.tredence.digitalbanking.common.exception.BadRequestException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

@SpringBootTest
@Transactional
class TransactionServiceTest {

    @Autowired
    private AccountService accountService;

    @Autowired
    private TransactionService transactionService;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    private Account sourceAccount;
    private Account targetAccount;

    @BeforeEach
    void setUp() {
        User owner = userRepository.save(User.builder()
                .fullName("Ada Lovelace")
                .email("ada+" + System.nanoTime() + "@example.com")
                .password(passwordEncoder.encode("password123"))
                .role(Role.CUSTOMER)
                .build());

        sourceAccount = accountService.createAccount(owner, AccountType.CHECKING);
        targetAccount = accountService.createAccount(owner, AccountType.SAVINGS);
    }

    @Test
    void depositIncreasesBalance() {
        transactionService.deposit(sourceAccount.getAccountNumber(), new BigDecimal("100.00"));

        Account refreshed = accountService.getByAccountNumber(sourceAccount.getAccountNumber());
        assertThat(refreshed.getBalance()).isEqualByComparingTo("100.00");
    }

    @Test
    void withdrawFailsWhenFundsAreInsufficient() {
        assertThatThrownBy(() -> transactionService.withdraw(sourceAccount.getAccountNumber(), new BigDecimal("50.00")))
                .isInstanceOf(BadRequestException.class);
    }

    @Test
    void transferMovesFundsBetweenAccounts() {
        transactionService.deposit(sourceAccount.getAccountNumber(), new BigDecimal("200.00"));

        transactionService.transfer(
                sourceAccount.getAccountNumber(), targetAccount.getAccountNumber(), new BigDecimal("75.00"));

        assertThat(accountService.getByAccountNumber(sourceAccount.getAccountNumber()).getBalance())
                .isEqualByComparingTo("125.00");
        assertThat(accountService.getByAccountNumber(targetAccount.getAccountNumber()).getBalance())
                .isEqualByComparingTo("75.00");
    }
}
