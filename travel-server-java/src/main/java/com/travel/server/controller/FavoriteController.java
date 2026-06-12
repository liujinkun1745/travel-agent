package com.travel.server.controller;

import com.travel.server.entity.Favorite;
import com.travel.server.repository.FavoriteRepository;
import com.travel.server.vo.Result;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/favorites")
public class FavoriteController {

    private final FavoriteRepository favoriteRepository;

    public FavoriteController(FavoriteRepository favoriteRepository) {
        this.favoriteRepository = favoriteRepository;
    }

    /** 添加收藏 */
    @PostMapping
    public Result<?> add(@RequestBody Map<String, String> body) {
        Long userId = ChatHistoryController.getCurrentUserId();
        Favorite fav = new Favorite();
        fav.setUserId(userId);
        fav.setQuestion(body.get("question"));
        fav.setAnswer(body.get("answer"));
        favoriteRepository.save(fav);
        return Result.ok(Map.of("id", fav.getId(), "message", "收藏成功"));
    }

    /** 我的收藏列表 */
    @GetMapping
    public Result<?> list() {
        Long userId = ChatHistoryController.getCurrentUserId();
        return Result.ok(favoriteRepository.findByUserIdOrderByCreatedAtDesc(userId));
    }

    /** 删除收藏 */
    @DeleteMapping("/{id}")
    public Result<?> delete(@PathVariable Long id) {
        Long userId = ChatHistoryController.getCurrentUserId();
        favoriteRepository.deleteByUserIdAndId(userId, id);
        return Result.ok(Map.of("message", "已删除"));
    }
}
