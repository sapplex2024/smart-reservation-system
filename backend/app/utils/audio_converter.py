import io
import subprocess
import tempfile
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class AudioConverter:
    """音频格式转换工具"""
    
    @staticmethod
    def audio_to_pcm(audio_data: bytes, input_format: str = 'webm', sample_rate: int = 16000, channels: int = 1) -> Optional[bytes]:
        """
        将音频数据转换为PCM格式
        
        Args:
            audio_data: 音频数据（WebM、WAV等格式）
            input_format: 输入音频格式，默认'webm'
            sample_rate: 目标采样率，默认16000Hz
            channels: 声道数，默认1（单声道）
            
        Returns:
            PCM格式的音频数据，转换失败返回None
        """
        try:
            # 创建临时文件
            input_suffix = f'.{input_format}'
            with tempfile.NamedTemporaryFile(suffix=input_suffix, delete=False) as input_file:
                input_file.write(audio_data)
                input_file_path = input_file.name
            
            with tempfile.NamedTemporaryFile(suffix='.pcm', delete=False) as output_file:
                output_file_path = output_file.name
            
            try:
                # 使用ffmpeg进行转换
                cmd = [
                    'ffmpeg',
                    '-i', input_file_path,
                    '-f', 's16le',  # 16位小端格式
                    '-ar', str(sample_rate),  # 采样率
                    '-ac', str(channels),  # 声道数
                    '-y',  # 覆盖输出文件
                    output_file_path
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30  # 30秒超时
                )
                
                if result.returncode != 0:
                    logger.error(f"FFmpeg转换失败: {result.stderr}")
                    return None
                
                # 读取转换后的PCM数据
                with open(output_file_path, 'rb') as f:
                    pcm_data = f.read()
                
                logger.info(f"音频转换成功: {input_format.upper()}({len(audio_data)}字节) -> PCM({len(pcm_data)}字节)")
                return pcm_data
                
            finally:
                # 清理临时文件
                try:
                    os.unlink(input_file_path)
                    os.unlink(output_file_path)
                except:
                    pass
                    
        except subprocess.TimeoutExpired:
            logger.error("音频转换超时")
            return None
        except Exception as e:
            logger.error(f"音频转换失败: {e}")
            return None
    
    @staticmethod
    def webm_to_pcm(webm_data: bytes, sample_rate: int = 16000, channels: int = 1) -> Optional[bytes]:
        """兼容性方法：将WebM音频数据转换为PCM格式"""
        return AudioConverter.audio_to_pcm(webm_data, 'webm', sample_rate, channels)
    
    @staticmethod
    def wav_to_pcm(wav_data: bytes, sample_rate: int = 16000, channels: int = 1) -> Optional[bytes]:
        """将WAV音频数据转换为PCM格式"""
        return AudioConverter.audio_to_pcm(wav_data, 'wav', sample_rate, channels)
    
    @staticmethod
    def base64_webm_to_pcm(base64_webm: str, sample_rate: int = 16000, channels: int = 1) -> Optional[bytes]:
        """
        将base64编码的WebM音频转换为PCM格式
        
        Args:
            base64_webm: base64编码的WebM音频数据
            sample_rate: 目标采样率，默认16000Hz
            channels: 声道数，默认1（单声道）
            
        Returns:
            PCM格式的音频数据，转换失败返回None
        """
        try:
            import base64
            audio_data = base64.b64decode(base64_webm)
            return AudioConverter.webm_to_pcm(audio_data, sample_rate, channels)
        except Exception as e:
            logger.error(f"Base64解码失败: {e}")
            return None
    
    @staticmethod
    def is_ffmpeg_available() -> bool:
        """
        检查系统是否安装了ffmpeg
        
        Returns:
            True如果ffmpeg可用，否则False
        """
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False