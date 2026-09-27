from typing import List, Dict

from pydantic import BaseModel, Field


class GlobalState(BaseModel):
    """全局状态定义"""
    topic: str = Field(default="AI人工智能行业", description="新闻搜索主题")
    raw_news: List[dict] = Field(default=[], description="搜索到的原始新闻列表")
    top_news: List[dict] = Field(default=[], description="精选出的关键新闻列表")
    digest_message: str = Field(default="", description="格式化后的新闻日报文本")


class GraphInput(BaseModel):
    """工作流输入"""
    topic: str = Field(default="AI人工智能行业", description="新闻搜索主题，默认 AI 行业")


class GraphOutput(BaseModel):
    """工作流输出"""
    digest_message: str = Field(..., description="最终生成的 AI 行业要闻日报文本")
    top_news: List[dict] = Field(default=[], description="精选的 3 条关键新闻结构列表")


class SearchNewsInput(BaseModel):
    """搜索新闻节点输入"""
    topic: str = Field(..., description="新闻搜索主题")


class SearchNewsOutput(BaseModel):
    """搜索新闻节点输出"""
    raw_news: List[dict] = Field(default=[], description="搜索到的原始新闻列表")


class SelectNewsInput(BaseModel):
    """智能精选新闻节点输入"""
    raw_news: List[dict] = Field(default=[], description="搜索到的原始新闻列表")


class SelectNewsOutput(BaseModel):
    """智能精选新闻节点输出"""
    top_news: List[dict] = Field(default=[], description="精选出的关键新闻列表")


class FormatMessageInput(BaseModel):
    """格式化日报节点输入"""
    top_news: List[dict] = Field(default=[], description="精选出的关键新闻列表")


class FormatMessageOutput(BaseModel):
    """格式化日报节点输出"""
    digest_message: str = Field(..., description="格式化后的 AI 行业要闻日报文本")


class SendEmailInput(BaseModel):
    """发送邮件节点输入"""
    digest_message: str = Field(..., description="要发送的 AI 行业要闻日报文本")


class SendEmailOutput(BaseModel):
    """发送邮件节点输出"""
    send_result: str = Field(..., description="邮件发送结果描述")