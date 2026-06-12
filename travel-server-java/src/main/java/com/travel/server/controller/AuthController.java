package com.travel.server.controller;

import com.travel.server.dto.LoginRequestDTO;
import com.travel.server.entity.User;
import com.travel.server.repository.UserRepository;
import com.travel.server.security.JwtUtils;
import com.travel.server.vo.Result;
import jakarta.validation.Valid;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtils jwtUtils;

    public AuthController(UserRepository userRepository,
                          PasswordEncoder passwordEncoder,
                          JwtUtils jwtUtils) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtUtils = jwtUtils;
    }

    @PostMapping("/register")
    public Result<?> register(@Valid @RequestBody LoginRequestDTO request) {
        if (userRepository.existsByUsername(request.getUsername())) {
            return Result.fail(400, "用户名已存在");
        }

        User user = new User();
        user.setUsername(request.getUsername());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        userRepository.save(user);

        return Result.ok(Map.of("message", "注册成功"));
    }

    @PostMapping("/login")
    public Result<?> login(@Valid @RequestBody LoginRequestDTO request) {
        User user = userRepository.findByUsername(request.getUsername())
                .orElse(null);

        if (user == null || !passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            return Result.fail(401, "用户名或密码错误");
        }

        String token = jwtUtils.generateToken(user.getId(), user.getUsername());

        return Result.ok(Map.of(
                "token", token,
                "userId", user.getId(),
                "username", user.getUsername(),
                "nickname", user.getNickname() != null ? user.getNickname() : user.getUsername(),
                "avatar", user.getAvatar() != null ? user.getAvatar() : ""
        ));
    }
}
