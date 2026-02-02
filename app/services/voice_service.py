"""
语音服务模块
支持阿里云 DashScope 语音识别（ASR）
"""
import logging
import base64
import tempfile
import os
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class VoiceService:
    """语音服务类"""
    
    def __init__(self):
        self.mock_mode = settings.VOICE_MOCK
        if not self.mock_mode:
            try:
                # 导入 DashScope SDK
                import dashscope
                from dashscope.audio.asr import Recognition, RecognitionCallback
                dashscope.api_key = settings.DASHSCOPE_API_KEY
                self.dashscope = dashscope
                self.Recognition = Recognition
                logger.info("DashScope ASR 服务已初始化")
            except ImportError:
                logger.warning("DashScope SDK 未安装，启用 Mock 模式")
                self.mock_mode = True
            except Exception as e:
                logger.error(f"DashScope 初始化失败: {e}，启用 Mock 模式")
                self.mock_mode = True
    
    async def speech_to_text(self, audio_data: bytes, audio_format: str = "webm") -> Optional[str]:
        """
        语音识别（ASR）- 使用 DashScope
        
        Args:
            audio_data: 音频数据（二进制）
            audio_format: 音频格式（webm, pcm, wav, opus等）
        
        Returns:
            识别的文本，失败返回None
        """
        if self.mock_mode:
            return self._mock_speech_to_text(audio_data)
        
        try:
            logger.info(f"调用 DashScope ASR 服务，音频长度: {len(audio_data)} bytes, 格式: {audio_format}")
            
            # DashScope ASR 需要文件路径，保存临时文件
            with tempfile.NamedTemporaryFile(suffix=f'.{audio_format}', delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_file_path = tmp_file.name
            
            try:
                # 使用 DashScope 批量识别接口
                from dashscope.audio.asr import Transcription
                
                # 转换格式映射
                format_map = {
                    'webm': 'opus',  # webm 通常使用 opus 编码
                    'wav': 'wav',
                    'pcm': 'pcm',
                    'opus': 'opus',
                    'mp3': 'mp3',
                    'aac': 'aac'
                }
                
                dashscope_format = format_map.get(audio_format, 'opus')
                
                # 调用转写接口
                transcription = Transcription(
                    model='paraformer-v2',  # 使用批量转写模型
                    file_urls=[tmp_file_path],
                    language_hints=['zh', 'en']  # 支持中英文
                )
                
                result = transcription.call()
                
                if result.status_code == 200 and result.output:
                    # 获取转写结果
                    transcripts = result.output.get('results', [])
                    if transcripts:
                        text = transcripts[0].get('transcription_url') or transcripts[0].get('text', '')
                        logger.info(f"ASR 识别成功: {text}")
                        return text
                    else:
                        logger.warning("ASR 返回空结果")
                        return None
                else:
                    logger.error(f"ASR 调用失败: {result.status_code}, {result.message}")
                    return self._mock_speech_to_text(audio_data)  # 失败时降级到 Mock
                    
            finally:
                # 清理临时文件
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
            
        except Exception as e:
            logger.error(f"语音识别失败: {e}", exc_info=True)
            # 失败时返回 Mock 结果
            return self._mock_speech_to_text(audio_data)
    
    def _mock_speech_to_text(self, audio_data: bytes) -> str:
        """Mock ASR：返回固定文本"""
        # 根据音频长度生成不同的Mock文本
        if len(audio_data) < 1000:
            return "你好"
        elif len(audio_data) < 5000:
            return "这个岗位的工作地点在哪里？"
        else:
            return "请问贵公司对Python后端工程师的技术要求是什么？需要几年工作经验？"
    
    async def text_to_speech(
        self, 
        text: str, 
        voice: str = "xiaoyun",
        sample_rate: int = 16000
    ) -> Optional[bytes]:
        """
        语音合成（TTS）- 暂时使用 Mock 实现
        
        Args:
            text: 要合成的文本
            voice: 发音人（xiaoyun, xiaogang等）
            sample_rate: 采样率
        
        Returns:
            音频数据（二进制），失败返回None
        """
        # 暂时返回 None，因为微信风格的语音消息主要是接收语音+展示文字
        # AI 回复以文字为主，不需要语音合成
        logger.info(f"TTS 请求（暂未实现）: {text[:50]}...")
        return None


# 全局实例
voice_service = VoiceService()
