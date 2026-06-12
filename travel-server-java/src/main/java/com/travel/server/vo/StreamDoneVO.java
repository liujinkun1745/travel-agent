package com.travel.server.vo;

/**
 * SSE 流式完成信号
 */
public class StreamDoneVO {

    private String type;

    public StreamDoneVO() {
        this.type = "done";
    }

    public String getType() { return type; }
}
