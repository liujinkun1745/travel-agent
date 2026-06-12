package com.travel.server.vo;

/**
 * SSE 流式数据块
 */
public class StreamChunkVO {

    private String type;
    private String content;

    public StreamChunkVO() {}

    public StreamChunkVO(String content) {
        this.type = "chunk";
        this.content = content;
    }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }
    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }
}
