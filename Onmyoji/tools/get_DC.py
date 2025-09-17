import win32gui
import win32ui
import win32con
import win32api
import numpy as np
import cv2
import pyautogui
import random
from PIL import Image, ImageEnhance, ImageFilter
from typing import Optional, Tuple, Union, List
from .WindowChecker import WindowChecker

class WindowCapture:
    def __init__(self, window_title: Optional[str] = None, hwnd: Optional[int] = None):
        # 复用WindowChecker类获取窗口信息
        self.checker = WindowChecker()
        self.hwnd = None
        
        # 设置窗口句柄或标题
        if hwnd:
            self.hwnd = hwnd
            self.checker.set_window_handle(hwnd)
        elif window_title:
            self.checker.set_window_title(window_title)
            self.hwnd = win32gui.FindWindow(None, window_title)
            if not self.hwnd:
                raise Exception(f"未找到窗口: {window_title}")
        else:
            # 如果未提供窗口标题和句柄，使用当前活动窗口
            self.hwnd = win32gui.GetForegroundWindow()
            self.checker.set_window_handle(self.hwnd)
        
        # 获取窗口客户区信息
        self.client_rect = win32gui.GetClientRect(self.hwnd)
        self.client_width = self.client_rect[2] - self.client_rect[0]
        self.client_height = self.client_rect[3] - self.client_rect[1]
        
        # 计算客户区在屏幕中的左上角位置
        client_top_left = win32gui.ClientToScreen(self.hwnd, (0, 0))
        self.client_left = client_top_left[0]
        self.client_top = client_top_left[1]
        
        # 初始化窗口状态标志
        self._minimized_manually_restored = False
    
    def get_window_info(self) -> Optional[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]]:
        """
        获取窗口的位置和尺寸信息
        复用WindowChecker的get_window_info方法
        """
        return self.checker.get_window_info()
        
    def capture_minimized_window(self) -> Optional[np.ndarray]:
        """
        尝试在不恢复窗口的情况下捕获最小化窗口的内容
        
        这个方法使用PrintWindow API尝试直接从最小化窗口获取内容，无需临时恢复窗口到前台
        
        返回:
            如果捕获成功，返回窗口的OpenCV图像数据
            如果捕获失败，返回None
        """
        try:
            # 获取窗口信息以获取尺寸
            window_info = self.get_window_info()
            if not window_info:
                print("无法获取窗口信息")
                return None
            
            # 解构窗口信息
            _, _, (width, height) = window_info
            
            # 检查窗口是否确实处于最小化状态
            if not win32gui.IsIconic(self.hwnd):
                print("窗口未处于最小化状态，使用常规截图方法")
                return self.capture_window_bitblt()
            
            print("尝试在不恢复窗口的情况下捕获最小化窗口内容...")
            
            # 创建设备上下文和位图对象
            hdc = win32gui.GetDC(self.hwnd)
            dc_obj = win32ui.CreateDCFromHandle(hdc)
            mem_dc = dc_obj.CreateCompatibleDC()
            
            # 创建位图对象
            bmp = win32ui.CreateBitmap()
            bmp.CreateCompatibleBitmap(dc_obj, width, height)
            mem_dc.SelectObject(bmp)
            
            # 尝试使用PrintWindow API获取最小化窗口内容
            # 使用PRF_CLIENT标志只获取客户区
            result = win32api.SendMessage(
                self.hwnd, 
                win32con.WM_PRINT, 
                mem_dc.GetSafeHdc(), 
                win32con.PRF_CLIENT | win32con.PRF_CHILDREN | win32con.PRF_ERASEBKGND
            )

            # 将位图转换为OpenCV图像
            try:
                signed_ints_array = bmp.GetBitmapBits(True)
                img = np.frombuffer(signed_ints_array, dtype='uint8')
                img.shape = (height, width, 4)
                
                # 转换为RGB格式（丢弃Alpha通道）
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
                # 检查图像是否有效（不是全黑或全白）
                if np.mean(img) < 10 or np.mean(img) > 245:
                    print("捕获的图像可能无效（过暗或过亮）")
                    # 不返回，继续尝试其他方法
                else:
                    print("成功在不恢复窗口的情况下捕获最小化窗口内容")
                    return img
            except Exception as e:
                print(f"处理位图数据时发生错误: {str(e)}")
            
            # 如果第一种方法失败，尝试使用备用方法
            print("尝试备用方法获取最小化窗口内容...")
            
            # 清理资源
            mem_dc.DeleteDC()
            dc_obj.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, hdc)
            
            # 备用方法：尝试创建一个临时的兼容DC
            hWndDC = win32gui.GetDC(self.hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hWndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            # 尝试使用BitBlt
            try:
                saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
                
                # 获取位图信息
                bmpinfo = saveBitMap.GetInfo()
                bmpstr = saveBitMap.GetBitmapBits(True)
                
                # 生成图像
                img = np.frombuffer(bmpstr, dtype='uint8').reshape((height, width, 4))
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
                # 检查图像是否有效
                if np.mean(img) > 10:
                    print("使用备用方法成功捕获最小化窗口内容")
                    return img
            except Exception as e:
                print(f"备用方法失败: {str(e)}")
            
            print("无法在不恢复窗口的情况下捕获最小化窗口内容")
            return None
        except Exception as e:
            print(f"捕获最小化窗口内容时发生错误: {str(e)}")
            return None
        finally:
            # 清理资源
            try:
                saveBitMap.DeleteObject()
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(self.hwnd, hWndDC)
            except:
                pass
    
    def capture_window_bitblt(self, region: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """
        使用BitBlt方法捕获窗口图像，即使窗口被遮挡或在后台
        
        参数:
            region: 可选的捕获区域 (left, top, width, height)，相对于窗口客户区
                    如果为None，则捕获整个客户区
        
        返回:
            如果捕获成功，返回窗口的OpenCV图像数据
            如果捕获失败，返回None
        """
        try:
            # 检查窗口是否最小化
            is_minimized = win32gui.IsIconic(self.hwnd)
            if is_minimized:
                # 首先尝试不恢复窗口的方法
                result = self.capture_minimized_window()
                if result is not None:
                    return result
                
                # 如果不恢复窗口的方法失败，再使用传统的临时恢复窗口方法
                print("窗口处于最小化状态，临时恢复窗口...")
                # 恢复窗口
                win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
                # 标记为手动恢复的，后续需要恢复最小化状态
                self._minimized_manually_restored = True
                # 短暂延迟以确保窗口完全恢复
                import time
                time.sleep(0.1) 
            
            # 重新获取客户区尺寸，确保获取的是最新的尺寸
            self.client_rect = win32gui.GetClientRect(self.hwnd)
            self.client_width = self.client_rect[2] - self.client_rect[0]
            self.client_height = self.client_rect[3] - self.client_rect[1]
            
            # 检查窗口尺寸是否有效
            if self.client_width <= 0 or self.client_height <= 0:
                print("窗口客户区尺寸无效，尝试使用PrintWindow方法")
                return self.capture_window()
                
            # 确定捕获区域
            if region:
                left, top, width, height = region
            else:
                left, top = 0, 0
                width, height = self.client_width, self.client_height
            
            # 获取窗口的设备上下文
            hWndDC = win32gui.GetDC(self.hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hWndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            
            # 创建位图对象
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            
            # 将位图选入设备上下文
            saveDC.SelectObject(saveBitMap)
            
            # 使用BitBlt复制图像
            saveDC.BitBlt(
                (0, 0),
                (width, height),
                mfcDC,
                (left, top),
                win32con.SRCCOPY,
            )
            
            # 获取位图信息
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            
            # 生成图像（注意：Windows位图是BGRX格式）
            try:
                img = np.frombuffer(
                    bmpstr,
                    dtype='uint8'
                ).reshape((height, width, 4))
            except ValueError as e:
                print(f"图像数据重塑失败: {str(e)}")
                return None
            
            # 转换为RGB格式（丢弃Alpha通道）
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            return img
        except Exception as e:
            print(f"使用BitBlt捕获窗口图像时发生错误: {str(e)}")
            return None
        finally:
            # 如果窗口原本是最小化的，恢复最小化状态
            if self._minimized_manually_restored:
                win32gui.ShowWindow(self.hwnd, win32con.SW_MINIMIZE)
                self._minimized_manually_restored = False
            
            # 清理资源
            try:
                win32gui.DeleteObject(saveBitMap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(self.hwnd, hWndDC)
            except:
                pass
    
    def is_window_minimized(self) -> bool:
        """
        检查窗口是否处于最小化状态
        
        返回:
            bool: 如果窗口最小化，返回True；否则返回False
        """
        return win32gui.IsIconic(self.hwnd)
    
    def is_window_in_background(self) -> bool:
        """
        检查游戏窗口是否在后台
        
        返回:
            bool: 如果窗口在后台，返回True；否则返回False
        """
        # 获取窗口矩形坐标
        window_rect = win32gui.GetWindowRect(self.hwnd)
        
        # 检查窗口是否部分或完全在屏幕外（这通常意味着窗口在后台）
        if window_rect[0] < -9 or window_rect[1] < 0 or window_rect[2] < 0 or window_rect[3] < 0:
            return True
        
        # 另一种判断方法：检查窗口是否是当前活动窗口
        foreground_window = win32gui.GetForegroundWindow()
        if foreground_window != self.hwnd:
            return True
        
        return False
    
    def capture_window(self) -> Optional[np.ndarray]:
        """
        捕获窗口的完整图像，即使窗口被最小化或被遮挡
        
        返回:
            如果捕获成功，返回窗口的OpenCV图像数据
            如果捕获失败，返回None
        """
        # 获取窗口信息
        window_info = self.get_window_info()
        if not window_info:
            print("无法获取窗口信息")
            return None
        
        # 解构窗口信息
        _, _, (width, height) = window_info
        
        # 如果窗口被最小化，先临时恢复窗口状态
        is_minimized = win32gui.IsIconic(self.hwnd)
        if is_minimized:
            win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
            import time
            time.sleep(0.1)  # 短暂延迟以确保窗口完全恢复
        
        try:
            # 获取窗口的设备上下文
            hdc = win32gui.GetDC(self.hwnd)
            dc_obj = win32ui.CreateDCFromHandle(hdc)
            mem_dc = dc_obj.CreateCompatibleDC()
            
            # 创建位图对象
            bmp = win32ui.CreateBitmap()
            bmp.CreateCompatibleBitmap(dc_obj, width, height)
            mem_dc.SelectObject(bmp)
            
            # 使用更兼容的方式调用PrintWindow
            try:
                # 尝试从win32gui调用PrintWindow
                result = win32gui.PrintWindow(self.hwnd, mem_dc.GetSafeHdc(), 0)
                if not result:
                    print("PrintWindow调用失败")
                    return None
            except AttributeError:
                # 如果win32gui没有PrintWindow，尝试使用win32api的SendMessage
                try:
                    # 使用win32api的方式
                    result = win32api.SendMessage(self.hwnd, win32con.WM_PRINT, mem_dc.GetSafeHdc(), win32con.PRF_CLIENT | win32con.PRF_NONCLIENT | win32con.PRF_ERASEBKGND)
                except Exception as e:
                    print(f"使用替代方法捕获窗口失败: {str(e)}")
                    return None
            
            # 将位图转换为OpenCV图像
            signed_ints_array = bmp.GetBitmapBits(True)
            img = np.frombuffer(signed_ints_array, dtype='uint8')
            img.shape = (height, width, 4)
            
            # 转换为RGB格式（丢弃Alpha通道）
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            return img
        except Exception as e:
            print(f"捕获窗口图像时发生错误: {str(e)}")
            return None
        finally:
            # 清理资源
            try:
                mem_dc.DeleteDC()
                dc_obj.DeleteDC()
                win32gui.ReleaseDC(self.hwnd, hdc)
            except:
                pass
            
            # 如果窗口原本是最小化的，恢复最小化状态
            if is_minimized:
                win32gui.ShowWindow(self.hwnd, win32con.SW_MINIMIZE)
    
    def find_image(self, target_image: Union[str, Image.Image], threshold: float = 0.8, use_bitblt: bool = True) -> Optional[Tuple[int, int]]:
        """
        在窗口图像中查找指定的目标图像
        
        参数:
            target_image: 目标图像的文件路径或PIL Image对象
            threshold: 匹配阈值，范围0-1，值越高匹配越精确
            use_bitblt: 是否使用BitBlt方法进行截图（支持后台窗口）
        
        返回:
            如果找到匹配，返回一个元组(x, y)表示目标图像在窗口中的中心相对位置
            如果未找到匹配，返回None
        """
        # 使用优化的图像识别方法
        return self.find_image_precise(target_image, threshold=threshold, use_bitblt=use_bitblt)
        
    def find_image_precise(self, target_image: Union[str, Image.Image], threshold: float = 0.8, 
                         grayscale: bool = True, confidence: float = None, 
                         enhance_contrast: bool = True, contrast_factor: float = 1.2, 
                         blur_level: int = 0, use_bitblt: bool = True, skip_preprocessing: bool = False) -> Optional[Tuple[int, int]]:
        """
        基于pyautogui底层逻辑的精确图像识别函数
        优化了模板匹配算法，增加了图像预处理选项，提高识别准确性
        
        参数:
            target_image: 目标图像的文件路径或PIL Image对象
            threshold: 匹配阈值，范围0-1
            grayscale: 是否转为灰度图进行匹配（提高速度和鲁棒性）
            confidence: 同threshold
            enhance_contrast: 是否增强对比度（提高识别率）
            contrast_factor: 对比度增强因子，建议范围1.0-1.5，1.0表示不增强
            blur_level: 模糊程度，0表示不模糊，>0表示应用高斯模糊（减少噪声干扰）
            use_bitblt: 是否使用BitBlt方法进行截图（支持后台窗口）
            skip_preprocessing: 是否完全跳过图像预处理（使用原始RGB图像进行匹配）
        
        返回:
            如果找到匹配，返回一个元组(x, y)表示目标图像在窗口中的中心相对位置
            如果未找到匹配，返回None
        """
        # 使用传入的confidence覆盖threshold
        if confidence is not None:
            threshold = confidence
            
        # 根据use_bitblt参数选择截图方法
        if use_bitblt:
            window_image = self.capture_window_bitblt()
        else:
            window_image = self.capture_window()
            
        if window_image is None:
            print("无法捕获窗口图像")
            return None
        
        # 读取目标图像
        if isinstance(target_image, str):
            target = cv2.imread(target_image)
        elif isinstance(target_image, Image.Image):
            # 转换PIL Image到OpenCV格式
            target = cv2.cvtColor(np.array(target_image), cv2.COLOR_RGB2BGR)
        else:
            raise TypeError("target_image必须是文件路径或PIL Image对象")
        
        # 检查目标图像是否有效
        if target is None:
            raise Exception("无法读取目标图像")
        
        # 检查窗口图像尺寸是否大于目标图像
        if window_image.shape[0] < target.shape[0] or window_image.shape[1] < target.shape[1]:
            print("窗口图像尺寸小于目标图像，无法进行匹配")
            return None
        
        # 如果跳过预处理，直接使用原始RGB图像进行匹配
        if skip_preprocessing:
            # 直接使用彩色图进行匹配
            result = cv2.matchTemplate(window_image, target, cv2.TM_CCOEFF_NORMED)
            min_val, best_max_val, min_loc, best_max_loc = cv2.minMaxLoc(result)
        else:
            # 图像预处理
            # 1. 转为灰度图
            if grayscale:
                window_image_gray = cv2.cvtColor(window_image, cv2.COLOR_BGR2GRAY)
                target_gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
                
                # 2. 增强对比度，但限制增强强度以避免图像失真
                if enhance_contrast and contrast_factor > 1.0:
                    # 确保对比度因子在合理范围内
                    contrast_factor = max(1.0, min(1.5, contrast_factor))
                    
                    # 转换为PIL Image进行对比度增强
                    pil_window = Image.fromarray(window_image_gray)
                    enhancer = ImageEnhance.Contrast(pil_window)
                    pil_window_enhanced = enhancer.enhance(contrast_factor)
                    window_image_gray = np.array(pil_window_enhanced)
                    
                    pil_target = Image.fromarray(target_gray)
                    enhancer = ImageEnhance.Contrast(pil_target)
                    pil_target_enhanced = enhancer.enhance(contrast_factor)
                    target_gray = np.array(pil_target_enhanced)
                
                # 3. 应用高斯模糊
                if blur_level > 0:
                    ksize = (blur_level * 2 + 1, blur_level * 2 + 1)  # 确保核大小为奇数
                    window_image_gray = cv2.GaussianBlur(window_image_gray, ksize, 0)
                    target_gray = cv2.GaussianBlur(target_gray, ksize, 0)
                
                # 尝试多种匹配算法
                methods = [
                    cv2.TM_CCOEFF_NORMED,  # 相关系数归一化匹配
                    cv2.TM_CCORR_NORMED,   # 相关匹配
                    cv2.TM_SQDIFF_NORMED   # 平方差匹配
                ]
                
                best_max_val = -1
                best_max_loc = (0, 0)
                
                for method in methods:
                    if method == cv2.TM_SQDIFF_NORMED:
                        # 对于平方差匹配，最小值表示最佳匹配
                        result = cv2.matchTemplate(window_image_gray, target_gray, method)
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                        # 转换为类似其他方法的值范围（越高越好）
                        current_score = 1 - min_val
                        current_loc = min_loc
                    else:
                        # 对于其他方法，最大值表示最佳匹配
                        result = cv2.matchTemplate(window_image_gray, target_gray, method)
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                        current_score = max_val
                        current_loc = max_loc
                    
                    # 更新最佳匹配
                    if current_score > best_max_val:
                        best_max_val = current_score
                        best_max_loc = current_loc
            else:
                # 不使用灰度图，直接使用彩色图
                result = cv2.matchTemplate(window_image, target, cv2.TM_CCOEFF_NORMED)
                min_val, best_max_val, min_loc, best_max_loc = cv2.minMaxLoc(result)
        
        # 如果匹配度大于阈值，返回匹配位置
        if best_max_val >= threshold:
            # 计算目标图像中心位置
            center_x = best_max_loc[0] + target.shape[1] // 2
            center_y = best_max_loc[1] + target.shape[0] // 2
            
            # 添加轻微的随机偏移，避免总是点击完全相同的位置
            center_x += random.randint(-2, 2)
            center_y += random.randint(-2, 2)
            
            # print(f"找到图像，位置: ({center_x}, {center_y})，匹配度: {best_max_val:.2f}")
            return (center_x, center_y)
        
        # print(f"未找到图像，最高匹配度: {best_max_val:.2f} 低于阈值: {threshold}")
        return None

# 示例用法
if __name__ == "__main__":
    try:
        window_title = "阴阳师-网易游戏"
        wc = WindowCapture(window_title)
        
        # 检查窗口是否在后台
        is_background = wc.is_window_in_background()
        print(f"窗口是否在后台: {is_background}")
        
        # 检查窗口是否最小化
        is_minimized = wc.is_window_minimized()
        print(f"窗口是否最小化: {is_minimized}")
        
        # 捕获窗口图像（使用BitBlt方法，支持后台和最小化窗口）
        print("正在使用BitBlt方法捕获窗口图像...")
        window_img = wc.capture_window_bitblt()
        
        if window_img is not None:
            print(f"成功捕获窗口图像，尺寸: {window_img.shape}")
            
            # 可选：显示捕获的图像
            # cv2.imshow("Window Capture (BitBlt)", window_img)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()
        else:
            print("无法捕获窗口图像")
        
        # 替换为你的目标图像路径
        # target_image_path = "path/to/your/image.png"
        
        # 使用BitBlt方法查找图像
        # position = wc.find_image(target_image_path, threshold=0.7, use_bitblt=True)
        
        # if position:
        #     print(f"找到图像，位置: {position}")
        # else:
        #     print("未找到图像")
            
    except Exception as e:
        print(f"发生错误: {str(e)}")