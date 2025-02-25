from django.db import models
from django.utils import timezone


class ChatLog(models.Model):
    session_id = models.CharField(
        max_length=100, verbose_name="세션 ID", db_column="SESSION_ID", default=""
    )
    message = models.TextField(
        verbose_name="대화 내용",
        null=False,
        blank=False,
        db_column="MSG_CN",
        default="",
    )
    is_user = models.BooleanField(
        verbose_name="사용자 여부",
        default=True,
        db_column="IS_USER_YN",
    )
    timestamp = models.DateTimeField(
        verbose_name="생성 시간",
        auto_now_add=True,  # default 제거
        db_column="CRT_DTM",
        null=True,  # 임시로 null 허용
    )

    def __str__(self):
        sender = "사용자" if self.is_user else "AI"
        return f"{sender}: {self.message[:50]}..."

    class Meta:
        db_table = "chat_logs"
        verbose_name = "대화 기록"
        verbose_name_plural = "대화 기록"
        ordering = ["timestamp"]
