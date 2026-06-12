package com.travel.server.vo;

/**
 * SSE 流式错误信号
 */
public class StreamErrorVO {

    private String type;
    private String error;

    public StreamErrorVO() {}

    public StreamErrorVO(String error) {
        this.type = "error";
        this.error = error;
    }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }
    public String getError() { return error; }
    public void setError(String error) { this.error = error; }
}
