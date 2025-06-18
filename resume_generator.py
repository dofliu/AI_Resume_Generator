#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI履歷生成器 - 支援應徵資料與學習歷程
使用Gemini API生成個人化內容
"""

from flask import Flask, render_template, request, jsonify, send_file
import random
import os
import json
import zipfile
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import threading
import time
import google.generativeai as genai

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ai_resume_generator_2024'

# 存儲生成進度的全域變數
generation_progress = {}

class AIResumeGenerator:
    def __init__(self):
        """初始化AI履歷生成器"""
        self.setup_fonts()
        self.init_data()
        self.setup_gemini()
        
    def setup_gemini(self):
        """設定Gemini API"""
        # 請在這裡設定您的Gemini API Key
        # 可以從環境變數讀取: os.getenv('GEMINI_API_KEY')
        # 或直接設定: genai.configure(api_key='your-api-key-here')
        
        try:
            # 嘗試從環境變數讀取API Key
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')
                self.gemini_available = True
                print("✅ Gemini API 已成功連接")
            else:
                print("⚠️  未找到GEMINI_API_KEY環境變數，將使用模板內容")
                self.gemini_available = False
        except Exception as e:
            print(f"❌ Gemini API 設定失敗: {e}")
            print("💡 將使用模板內容作為備用方案")
            self.gemini_available = False
    
    def setup_fonts(self):
        """設定中文字體"""
        try:
            font_paths = [
                'NotoSansCJK-Regular.ttc',
                'NotoSansTC-Regular.otf',
                'TaipeiSansTCBeta-Regular.ttf',
                '/System/Library/Fonts/PingFang.ttc',
                'C:/Windows/Fonts/msjh.ttc',
            ]
            
            self.font_loaded = False
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        self.font_loaded = True
                        print(f"成功載入字體: {font_path}")
                        break
                    except:
                        continue
                        
        except Exception as e:
            print(f"字體設定錯誤: {e}")
    
    def init_data(self):
        """初始化資料庫"""
        self.names = {
            'surnames': ['王', '李', '張', '劉', '陳', '楊', '趙', '黃', '周', '吳', 
                        '徐', '孫', '胡', '朱', '高', '林', '何', '郭', '馬', '羅'],
            'given_names': ['志明', '雅婷', '怡君', '建宏', '淑芬', '俊傑', '美玲', 
                           '志偉', '麗華', '承翰', '佳蓉', '宗翰', '雅慧', '家豪', 
                           '文欣', '俊宏', '婉琪', '家駿', '詩涵', '宇軒']
        }
        
        self.cities = ['台北市', '新北市', '桃園市', '台中市', '台南市', '高雄市', 
                      '基隆市', '新竹市', '嘉義市', '新竹縣', '苗栗縣', '彰化縣', 
                      '南投縣', '雲林縣', '嘉義縣', '屏東縣', '宜蘭縣', '花蓮縣', '台東縣']
        
        self.universities = ['國立台灣大學', '國立清華大學', '國立交通大學', '國立成功大學',
                           '國立政治大學', '國立中央大學', '國立中山大學', '國立中興大學',
                           '輔仁大學', '東吳大學', '淡江大學', '世新大學', '銘傳大學',
                           '文化大學', '逢甲大學', '東海大學']
        
        self.high_schools = ['建國中學', '北一女中', '師大附中', '成功高中', '中山女中',
                           '大同高中', '景美女中', '松山高中', '板橋高中', '桃園高中',
                           '新竹高中', '台中一中', '台中女中', '彰化高中', '台南一中',
                           '台南女中', '高雄中學', '雄女中學']
        
        # 職位和科系對應
        self.majors = {
            'software': ['資訊工程學系', '資訊管理學系', '電機工程學系', '數學系', '統計學系', '電子工程學系'],
            'marketing': ['企業管理學系', '行銷學系', '廣告學系', '大眾傳播學系', '國際貿易學系', '商業設計學系'],
            'finance': ['財務金融學系', '會計學系', '經濟學系', '國際企業學系', '統計學系', '應用數學系'],
            'hr': ['人力資源管理學系', '企業管理學系', '心理學系', '社會學系', '勞工關係學系', '工商管理學系'],
            'design': ['視覺傳達設計學系', '工業設計學系', '多媒體設計學系', '資訊傳播學系', '美術學系', '建築學系'],
            'sales': ['企業管理學系', '國際貿易學系', '行銷學系', '經濟學系', '商業管理學系', '觀光事業學系']
        }
        
        # 學生學習歷程相關科系
        self.student_majors = {
            'science': ['物理學系', '化學系', '生物學系', '數學系', '地質學系', '大氣科學系'],
            'engineering': ['機械工程學系', '電機工程學系', '化學工程學系', '土木工程學系', '材料科學系'],
            'medical': ['醫學系', '牙醫學系', '藥學系', '護理學系', '物理治療學系', '職能治療學系'],
            'business': ['企業管理學系', '會計學系', '財務金融學系', '經濟學系', '國際企業學系'],
            'liberal_arts': ['中國文學系', '外國語文學系', '歷史學系', '哲學系', '社會學系', '心理學系'],
            'arts': ['美術學系', '音樂學系', '戲劇學系', '舞蹈學系', '設計學系']
        }
        
        # 個人特質選項
        self.personality_traits = {
            '工作態度': ['積極主動', '被動', '認真負責', '隨性', '完美主義', '實用主義'],
            '社交性向': ['外向', '內向', '樂觀', '悲觀', '健談', '內斂'],
            '技術偏好': ['硬體導向', '軟體導向', '理論研究', '實作應用', '創新思維', '穩健執行'],
            '學習風格': ['視覺學習', '聽覺學習', '動手實作', '邏輯分析', '創意發想', '系統化學習'],
            '合作方式': ['團隊合作', '獨立作業', '領導他人', '跟隨指導', '跨域協作', '專精領域'],
            '問題解決': ['邏輯分析', '直覺判斷', '創意思考', '經驗導向', '數據導向', '人文關懷']
        }
        
        self.companies = {
            'software': ['台積電', '聯發科技', '華碩電腦', '宏碁集團', '廣達電腦', '仁寶電腦',
                        '鴻海精密', '和碩聯合', '緯創資通', '英業達', '神通資科', '資策會',
                        '中華電信', '遠傳電信'],
            'marketing': ['統一企業', '7-Eleven', '全家便利商店', '誠品書店', '遠東百貨',
                         '新光三越', '奧美廣告', '電通安吉斯', 'Yahoo奇摩', 'Google台灣'],
            'finance': ['台灣銀行', '第一銀行', '華南銀行', '兆豐銀行', '富邦金控', '國泰金控',
                       '中信金控', '玉山銀行', '台新銀行', '元大金控'],
            'hr': ['104人力銀行', '1111人力銀行', 'yes123', '萬寶華', '藝珂人事'],
            'design': ['奧美廣告', '電通安吉斯', '博思廣告', 'HTC', '華碩設計'],
            'sales': ['台灣大哥大', '中華電信', '遠傳電信', '信義房屋', '永慶房屋']
        }

    def generate_name(self):
        return random.choice(self.names['surnames']) + random.choice(self.names['given_names'])

    def generate_basic_info(self, document_type):
        """生成基本資訊"""
        name = self.generate_name()
        city = random.choice(self.cities)
        
        if document_type == 'job_application':
            age = random.randint(22, 45)
        else:  # student_portfolio
            age = random.randint(16, 19)
        
        return {
            'name': name,
            'city': city,
            'age': age,
            'email': f"{name.lower().replace(' ', '')}@email.com",
            'phone': f'09{random.randint(10000000, 99999999)}'
        }

    def select_personality_traits(self, custom_traits=None):
        """選擇個人特質"""
        if custom_traits:
            return custom_traits
        
        # 隨機選擇特質
        selected_traits = {}
        for category, traits in self.personality_traits.items():
            selected_traits[category] = random.choice(traits)
        
        return selected_traits

    def generate_with_gemini(self, prompt, fallback_content=""):
        """使用Gemini API生成內容"""
        if not self.gemini_available:
            return fallback_content
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini API 調用失敗: {e}")
            return fallback_content

    def create_job_application_prompt(self, basic_info, job_type, company_name, personality_traits, education_level):
        """創建求職履歷的Gemini提示"""
        traits_text = ", ".join([f"{k}: {v}" for k, v in personality_traits.items()])
        
        prompt = f"""
請為以下求職者生成一份完整的中文履歷內容：

基本資訊：
- 姓名：{basic_info['name']}
- 年齡：{basic_info['age']}歲
- 居住地：{basic_info['city']}
- 應徵職位：{job_type}
- 目標公司：{company_name}
- 個人特質：{traits_text}
- 教育程度：{education_level}

請生成以下內容，每個項目用「===」分隔：

1. 學歷背景（包含大學名稱、科系、就讀時間、GPA）
2. 語言能力（英文程度、相關測驗成績、其他語言）
3. 工作經驗（公司名稱、職位、工作時間、工作內容描述）
4. 專業技能（技術技能及熟練程度）
5. 證照資格（相關專業證照）
6. 專案經驗（專案名稱、描述、使用技術、團隊規模、擔任角色）
7. 個人特質描述（基於提供的特質，寫一段個人特質說明）
8. 對公司願景（對目標公司的看法和期待）

請確保內容：
- 符合台灣就業環境
- 反映個人特質
- 具有真實感和個人化
- 適合{job_type}職位
- 使用繁體中文
"""
        return prompt

    def create_student_portfolio_prompt(self, basic_info, target_major, personality_traits):
        """創建學生學習歷程的Gemini提示"""
        traits_text = ", ".join([f"{k}: {v}" for k, v in personality_traits.items()])
        
        prompt = f"""
請為以下學生生成一份完整的中文學習歷程內容：

基本資訊：
- 姓名：{basic_info['name']}
- 年齡：{basic_info['age']}歲
- 居住地：{basic_info['city']}
- 目標科系：{target_major}
- 個人特質：{traits_text}

請生成以下內容，每個項目用「===」分隔：

1. 學業表現（高中學校、主要科目成績、班級排名、特殊學術表現）
2. 語言能力（英文程度、相關測驗成績、其他語言學習）
3. 課外活動（社團參與、擔任幹部經驗、活動組織經驗）
4. 競賽經驗（學科競賽、技能競賽、獲獎記錄）
5. 志工服務（志工活動參與、服務時數、服務心得）
6. 專題研究（研究主題、研究方法、研究成果、指導老師）
7. 個人特質描述（基於提供的特質，寫一段個人特質說明）
8. 學習動機（對目標科系的興趣和學習規劃）

請確保內容：
- 符合台灣高中生背景
- 反映個人特質
- 具有真實感和個人化
- 適合{target_major}科系申請
- 展現學習熱忱和潛力
- 使用繁體中文
"""
        return prompt

    def parse_gemini_response(self, response_text):
        """解析Gemini回應"""
        sections = response_text.split('===')
        parsed_content = {}
        
        section_names = [
            'education', 'language_skills', 'experience', 'technical_skills',
            'certificates', 'projects', 'personality', 'vision'
        ]
        
        for i, section in enumerate(sections):
            if i < len(section_names) and section.strip():
                parsed_content[section_names[i]] = section.strip()
        
        return parsed_content

    def generate_fallback_content(self, document_type, job_type_or_major, basic_info, personality_traits):
        """生成備用內容（當Gemini不可用時）"""
        content = {
            'education': f"{random.choice(self.universities)} - {random.choice(self.majors.get(job_type_or_major, ['通用學系']))} (學士)\n2019-2023 | GPA: {random.uniform(3.0, 4.0):.2f}/4.0",
            'language_skills': f"英文: 中上 (TOEIC: {random.randint(650, 850)})\n日文: 基礎",
            'personality': f"我是一個{personality_traits.get('工作態度', '積極主動')}且{personality_traits.get('社交性向', '樂觀')}的人。",
            'vision': "希望能在貴公司發揮所長，與團隊共同成長。"
        }
        
        if document_type == 'job_application':
            content.update({
                'experience': f"{random.choice(self.companies.get(job_type_or_major, ['科技公司']))} - 專員\n2023.01 - 至今\n負責相關業務推展",
                'technical_skills': "Microsoft Office: 熟練\nPython: 中等",
                'certificates': "相關專業證照",
                'projects': "專案名稱：系統優化\n描述：提升系統效能\n技術：Python, SQL"
            })
        else:  # student_portfolio
            content.update({
                'experience': "學生會幹部 - 活動組組員\n2022.09 - 2023.06\n協助籌辦校內大型活動",
                'technical_skills': "程式設計: 基礎\n資料分析: 中等",
                'certificates': "英檢中級初試通過",
                'projects': "專題研究：環保議題探討\n方法：問卷調查、文獻回顧\n成果：校內科展優選"
            })
        
        return content

    def generate_document(self, document_type, params):
        """生成文件內容"""
        basic_info = self.generate_basic_info(document_type)
        personality_traits = self.select_personality_traits(params.get('personality_traits'))
        
        if document_type == 'job_application':
            job_type = params.get('job_type', 'software')
            company_name = params.get('company_name', '科技創新股份有限公司')
            education_level = params.get('education_level', '學士')
            
            prompt = self.create_job_application_prompt(
                basic_info, job_type, company_name, personality_traits, education_level
            )
            
            if self.gemini_available:
                try:
                    response = self.generate_with_gemini(prompt)
                    content = self.parse_gemini_response(response)
                except:
                    content = self.generate_fallback_content(document_type, job_type, basic_info, personality_traits)
            else:
                content = self.generate_fallback_content(document_type, job_type, basic_info, personality_traits)
                
        else:  # student_portfolio
            target_major = params.get('target_major', 'engineering')
            major_name = random.choice(self.student_majors.get(target_major, ['通用學系']))
            
            prompt = self.create_student_portfolio_prompt(
                basic_info, major_name, personality_traits
            )
            
            if self.gemini_available:
                try:
                    response = self.generate_with_gemini(prompt)  # 移除 await
                    content = self.parse_gemini_response(response)
                except:
                    content = self.generate_fallback_content(document_type, job_type, basic_info, personality_traits)
        
        return {
            'basic_info': basic_info,
            'personality_traits': personality_traits,
            'content': content,
            'document_type': document_type
        }

    def create_pdf_styles(self):
        """創建PDF樣式"""
        styles = getSampleStyleSheet()
        
        try:
            pdfmetrics.getFont('ChineseFont')
            font_name = 'ChineseFont'
        except:
            font_name = 'Helvetica'
        
        custom_styles = {
            'Title': ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName=font_name
            ),
            'Heading': ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=12,
                fontName=font_name
            ),
            'Normal': ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                fontName=font_name
            )
        }
        
        return custom_styles

    def generate_pdf(self, document_data, filename):
        """生成PDF文件"""
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = self.create_pdf_styles()
        story = []
        
        basic_info = document_data['basic_info']
        content = document_data['content']
        document_type = document_data['document_type']
        
        # 標題
        if document_type == 'job_application':
            title = f"履歷表 - {basic_info['name']}"
        else:
            title = f"學習歷程檔案 - {basic_info['name']}"
            
        story.append(Paragraph(title, styles['Title']))
        story.append(Spacer(1, 12))
        
        # 基本資訊
        contact_info = [
            f"聯絡資訊：{basic_info['email']} | {basic_info['phone']}",
            f"居住地：{basic_info['city']} | 年齡：{basic_info['age']}歲"
        ]
        
        for info in contact_info:
            story.append(Paragraph(info, styles['Normal']))
        
        story.append(Spacer(1, 12))
        
        # 個人特質
        story.append(Paragraph("個人特質", styles['Heading']))
        traits_text = " | ".join([f"{k}: {v}" for k, v in document_data['personality_traits'].items()])
        story.append(Paragraph(traits_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # 根據文件類型添加相應內容
        if document_type == 'job_application':
            sections = [
                ('學歷背景', 'education'),
                ('語言能力', 'language_skills'),
                ('工作經驗', 'experience'),
                ('專業技能', 'technical_skills'),
                ('證照資格', 'certificates'),
                ('專案經驗', 'projects'),
                ('個人特質描述', 'personality'),
                ('對公司願景', 'vision')
            ]
        else:  # student_portfolio
            sections = [
                ('學業表現', 'education'),
                ('語言能力', 'language_skills'),
                ('課外活動', 'experience'),
                ('競賽經驗', 'technical_skills'),
                ('志工服務', 'certificates'),
                ('專題研究', 'projects'),
                ('個人特質描述', 'personality'),
                ('學習動機', 'vision')
            ]
        
        for section_title, section_key in sections:
            if section_key in content and content[section_key]:
                story.append(Paragraph(section_title, styles['Heading']))
                story.append(Paragraph(content[section_key], styles['Normal']))
                story.append(Spacer(1, 12))
        
        doc.build(story)

# 初始化生成器
generator = AIResumeGenerator()

@app.route('/')
def index():
    """主頁面"""
    return render_template('index.html', personality_traits=generator.personality_traits)

@app.route('/generate', methods=['POST'])
def generate_documents():
    """生成文件"""
    try:
        data = request.json
        count = int(data.get('count', 5))
        document_type = data.get('documentType', 'job_application')
        
        if count < 1 or count > 50:
            return jsonify({'error': '請輸入1-50之間的數量'}), 400
        
        # 生成任務ID
        task_id = f"task_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # 初始化進度
        generation_progress[task_id] = {
            'status': 'started',
            'progress': 0,
            'total': count,
            'documents': [],
            'message': '準備中...'
        }
        
        # 在背景執行生成任務
        def generate_task():
            try:
                import asyncio
                
                async def async_generate():
                    documents = []
                    
                    for i in range(count):
                        generation_progress[task_id]['progress'] = i + 1
                        generation_progress[task_id]['message'] = f'生成中... {i+1}/{count}'
                        
                        # 準備參數
                        params = {}
                        if document_type == 'job_application':
                            params = {
                                'job_type': data.get('jobType', 'software'),
                                'company_name': data.get('companyName', '科技創新股份有限公司'),
                                'education_level': data.get('educationLevel', '學士'),
                                'personality_traits': data.get('personalityTraits')
                            }
                        else:  # student_portfolio
                            params = {
                                'target_major': data.get('targetMajor', 'engineering'),
                                'personality_traits': data.get('personalityTraits')
                            }
                        
                        document = generator.generate_document(document_type, params)
                        documents.append(document)
                        
                        time.sleep(0.2)  # 避免API限制
                    
                    generation_progress[task_id]['status'] = 'completed'
                    generation_progress[task_id]['documents'] = documents
                    generation_progress[task_id]['message'] = '生成完成！'
                
                # 運行異步函數
                asyncio.run(async_generate())
                
            except Exception as e:
                generation_progress[task_id]['status'] = 'error'
                generation_progress[task_id]['message'] = str(e)
        
        # 啟動背景線程
        thread = threading.Thread(target=generate_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({'task_id': task_id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/progress/<task_id>')
def get_progress(task_id):
    """獲取生成進度"""
    if task_id not in generation_progress:
        return jsonify({'error': '任務不存在'}), 404
    
    return jsonify(generation_progress[task_id])

@app.route('/documents/<task_id>')
def get_documents(task_id):
    """獲取生成的文件列表"""
    if task_id not in generation_progress:
        return jsonify({'error': '任務不存在'}), 404
    
    task = generation_progress[task_id]
    if task['status'] != 'completed':
        return jsonify({'error': '任務尚未完成'}), 400
    
    # 只返回必要的資訊用於顯示
    document_list = []
    for i, document in enumerate(task['documents']):
        doc_summary = {
            'index': i,
            'basic_info': document['basic_info'],
            'personality_traits': document['personality_traits'],
            'content': document['content'],
            'document_type': document['document_type']
        }
        document_list.append(doc_summary)
    
    return jsonify({'documents': document_list})

@app.route('/download/<task_id>/<int:doc_index>')
def download_single_pdf(task_id, doc_index):
    """下載單份文件PDF"""
    if task_id not in generation_progress:
        return jsonify({'error': '任務不存在'}), 404
    
    task = generation_progress[task_id]
    if task['status'] != 'completed':
        return jsonify({'error': '任務尚未完成'}), 400
    
    if doc_index >= len(task['documents']):
        return jsonify({'error': '文件索引無效'}), 400
    
    document = task['documents'][doc_index]
    
    # 創建臨時PDF檔案
    temp_dir = tempfile.mkdtemp()
    doc_type_name = "履歷" if document['document_type'] == 'job_application' else "學習歷程"
    filename = f"{doc_type_name}_{document['basic_info']['name']}_{doc_index+1:03d}.pdf"
    filepath = os.path.join(temp_dir, filename)
    
    try:
        generator.generate_pdf(document, filepath)
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': f'PDF生成失敗: {str(e)}'}), 500

@app.route('/download_all/<task_id>')
def download_all_pdfs(task_id):
    """下載所有文件PDF (打包成ZIP)"""
    if task_id not in generation_progress:
        return jsonify({'error': '任務不存在'}), 404
    
    task = generation_progress[task_id]
    if task['status'] != 'completed':
        return jsonify({'error': '任務尚未完成'}), 400
    
    # 創建臨時目錄
    temp_dir = tempfile.mkdtemp()
    doc_type_name = "履歷集合" if task['documents'][0]['document_type'] == 'job_application' else "學習歷程集合"
    zip_filename = f"{doc_type_name}_{len(task['documents'])}份.zip"
    zip_filepath = os.path.join(temp_dir, zip_filename)
    
    try:
        with zipfile.ZipFile(zip_filepath, 'w') as zipf:
            for i, document in enumerate(task['documents']):
                doc_type_name = "履歷" if document['document_type'] == 'job_application' else "學習歷程"
                pdf_filename = f"{doc_type_name}_{document['basic_info']['name']}_{i+1:03d}.pdf"
                pdf_filepath = os.path.join(temp_dir, pdf_filename)
                
                generator.generate_pdf(document, pdf_filepath)
                zipf.write(pdf_filepath, pdf_filename)
                
                # 清理臨時PDF檔案
                os.remove(pdf_filepath)
        
        return send_file(zip_filepath, as_attachment=True, download_name=zip_filename)
        
    except Exception as e:
        return jsonify({'error': f'ZIP生成失敗: {str(e)}'}), 500

if __name__ == '__main__':
    # 創建templates目錄
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # 創建HTML模板
    html_template = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI履歷生成器 - 應徵資料與學習歷程</title>
    <style>
        body {
            font-family: 'Microsoft JhengHei', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 2.2em;
        }
        
        .controls {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        
        .control-group {
            display: flex;
            gap: 20px;
            align-items: center;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        
        .control-section {
            margin-bottom: 25px;
            padding: 15px;
            background: #fff;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }
        
        .control-section h3 {
            margin-top: 0;
            color: #667eea;
            font-size: 1.1em;
        }
        
        label {
            font-weight: bold;
            color: #555;
            min-width: 120px;
        }
        
        input, select {
            padding: 8px 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        
        .trait-group {
            margin-bottom: 10px;
        }
        
        .trait-options {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 5px;
        }
        
        .trait-option {
            padding: 5px 12px;
            background: #f0f0f0;
            border: 1px solid #ddd;
            border-radius: 15px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.3s ease;
        }
        
        .trait-option:hover {
            background: #e0e0e0;
        }
        
        .trait-option.selected {
            background: #667eea;
            color: white;
        }
        
        .btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s ease;
            margin: 5px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .document-type-toggle {
            display: flex;
            background: #f0f0f0;
            border-radius: 25px;
            padding: 5px;
            margin-bottom: 20px;
        }
        
        .document-type-option {
            flex: 1;
            padding: 10px 20px;
            text-align: center;
            cursor: pointer;
            border-radius: 20px;
            transition: all 0.3s ease;
        }
        
        .document-type-option.active {
            background: #667eea;
            color: white;
        }
        
        .progress-container {
            display: none;
            margin: 20px 0;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #f0f0f0;
            border-radius: 10px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(45deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.3s ease;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .stat-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        
        .document-preview {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 10px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .document-section {
            margin: 15px 0;
        }
        
        .document-section h3 {
            color: #667eea;
            border-bottom: 1px solid #eee;
            padding-bottom: 5px;
        }
        
        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI履歷生成器 - 應徵資料與學習歷程</h1>
        
        <div class="controls">
            <!-- 文件類型選擇 -->
            <div class="document-type-toggle">
                <div class="document-type-option active" data-type="job_application">
                    💼 求職履歷
                </div>
                <div class="document-type-option" data-type="student_portfolio">
                    🎓 學習歷程
                </div>
            </div>
            
            <!-- 基本設定 -->
            <div class="control-section">
                <h3>📋 基本設定</h3>
                <div class="control-group">
                    <label>生成數量：</label>
                    <input type="number" id="documentCount" value="5" min="1" max="50">
                </div>
            </div>
            
            <!-- 求職履歷專用設定 -->
            <div class="control-section" id="jobApplicationSettings">
                <h3>💼 求職履歷設定</h3>
                <div class="control-group">
                    <label>職位類型：</label>
                    <select id="jobType">
                        <option value="software">軟體工程師</option>
                        <option value="marketing">行銷專員</option>
                        <option value="finance">財務分析師</option>
                        <option value="hr">人力資源專員</option>
                        <option value="design">UI/UX設計師</option>
                        <option value="sales">業務代表</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>公司名稱：</label>
                    <input type="text" id="companyName" value="科技創新股份有限公司">
                </div>
                <div class="control-group">
                    <label>教育程度：</label>
                    <select id="educationLevel">
                        <option value="學士">學士</option>
                        <option value="碩士">碩士</option>
                        <option value="博士">博士</option>
                    </select>
                </div>
            </div>
            
            <!-- 學習歷程專用設定 -->
            <div class="control-section hidden" id="studentPortfolioSettings">
                <h3>🎓 學習歷程設定</h3>
                <div class="control-group">
                    <label>目標科系：</label>
                    <select id="targetMajor">
                        <option value="science">理學院 (物理、化學、生物)</option>
                        <option value="engineering">工學院 (機械、電機、化工)</option>
                        <option value="medical">醫學院 (醫學、牙醫、藥學)</option>
                        <option value="business">商學院 (企管、會計、經濟)</option>
                        <option value="liberal_arts">文學院 (中文、外語、歷史)</option>
                        <option value="arts">藝術學院 (美術、音樂、設計)</option>
                    </select>
                </div>
            </div>
            
            <!-- 個人特質設定 -->
            <div class="control-section">
                <h3>🎯 個人特質設定</h3>
                <p style="color: #666; font-size: 14px;">選擇個人特質，或留空讓系統隨機選擇</p>
                
                {% for category, traits in personality_traits.items() %}
                <div class="trait-group">
                    <label>{{ category }}：</label>
                    <div class="trait-options" data-category="{{ category }}">
                        {% for trait in traits %}
                        <div class="trait-option" data-trait="{{ trait }}">{{ trait }}</div>
                        {% endfor %}
                    </div>
                </div>
                {% endfor %}
            </div>
            
            <!-- 操作按鈕 -->
            <div class="control-group">
                <button class="btn" onclick="startGeneration()">🚀 生成文件</button>
                <button class="btn" onclick="downloadAllPDFs()" id="downloadBtn" disabled>📥 下載所有PDF</button>
                <button class="btn" onclick="clearResults()">🗑️ 清除結果</button>
                <button class="btn" onclick="randomizeTraits()" style="background: #28a745;">🎲 隨機特質</button>
            </div>
        </div>
        
        <div class="progress-container" id="progressContainer">
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <p id="progressText">準備中...</p>
        </div>
        
        <div class="stats" id="statsContainer" style="display: none;">
            <div class="stat-card">
                <div class="stat-number" id="totalCount">0</div>
                <div class="stat-label">總文件數</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="aiGenerated">0</div>
                <div class="stat-label">AI生成數</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="avgLength">0</div>
                <div class="stat-label">平均字數</div>
            </div>
        </div>
        
        <div id="previewArea" style="display: none;">
            <h2>📋 生成的文件預覽</h2>
            <div id="documentList"></div>
        </div>
    </div>

    <script>
        let currentTaskId = null;
        let currentDocumentType = 'job_application';
        
        // 文件類型切換
        document.querySelectorAll('.document-type-option').forEach(option => {
            option.addEventListener('click', function() {
                // 更新按鈕狀態
                document.querySelectorAll('.document-type-option').forEach(o => o.classList.remove('active'));
                this.classList.add('active');
                
                // 更新文件類型
                currentDocumentType = this.dataset.type;
                
                // 顯示/隱藏相應設定
                if (currentDocumentType === 'job_application') {
                    document.getElementById('jobApplicationSettings').classList.remove('hidden');
                    document.getElementById('studentPortfolioSettings').classList.add('hidden');
                } else {
                    document.getElementById('jobApplicationSettings').classList.add('hidden');
                    document.getElementById('studentPortfolioSettings').classList.remove('hidden');
                }
            });
        });
        
        // 特質選擇
        document.querySelectorAll('.trait-option').forEach(option => {
            option.addEventListener('click', function() {
                const category = this.parentElement.dataset.category;
                // 清除同類別的其他選擇
                this.parentElement.querySelectorAll('.trait-option').forEach(o => o.classList.remove('selected'));
                // 選擇當前選項
                this.classList.add('selected');
            });
        });
        
        // 隨機選擇特質
        function randomizeTraits() {
            document.querySelectorAll('.trait-options').forEach(group => {
                const options = group.querySelectorAll('.trait-option');
                // 清除所有選擇
                options.forEach(o => o.classList.remove('selected'));
                // 隨機選擇一個
                const randomOption = options[Math.floor(Math.random() * options.length)];
                randomOption.classList.add('selected');
            });
        }
        
        // 獲取選擇的特質
        function getSelectedTraits() {
            const traits = {};
            document.querySelectorAll('.trait-options').forEach(group => {
                const category = group.dataset.category;
                const selected = group.querySelector('.trait-option.selected');
                if (selected) {
                    traits[category] = selected.dataset.trait;
                }
            });
            return Object.keys(traits).length > 0 ? traits : null;
        }
        
        async function startGeneration() {
            const count = parseInt(document.getElementById('documentCount').value);
            
            if (count < 1 || count > 50) {
                alert('請輸入1-50之間的數量');
                return;
            }
            
            try {
                // 準備請求數據
                const requestData = {
                    count: count,
                    documentType: currentDocumentType,
                    personalityTraits: getSelectedTraits()
                };
                
                if (currentDocumentType === 'job_application') {
                    requestData.jobType = document.getElementById('jobType').value;
                    requestData.companyName = document.getElementById('companyName').value;
                    requestData.educationLevel = document.getElementById('educationLevel').value;
                } else {
                    requestData.targetMajor = document.getElementById('targetMajor').value;
                }
                
                // 發送生成請求
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestData)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    currentTaskId = result.task_id;
                    startProgressTracking();
                } else {
                    alert('錯誤: ' + result.error);
                }
                
            } catch (error) {
                alert('請求失敗: ' + error.message);
            }
        }
        
        function startProgressTracking() {
            document.getElementById('progressContainer').style.display = 'block';
            document.getElementById('previewArea').style.display = 'none';
            document.getElementById('statsContainer').style.display = 'none';
            
            const interval = setInterval(async () => {
                try {
                    const response = await fetch(`/progress/${currentTaskId}`);
                    const progress = await response.json();
                    
                    if (response.ok) {
                        const percentage = (progress.progress / progress.total) * 100;
                        document.getElementById('progressFill').style.width = percentage + '%';
                        document.getElementById('progressText').textContent = progress.message;
                        
                        if (progress.status === 'completed') {
                            clearInterval(interval);
                            document.getElementById('progressContainer').style.display = 'none';
                            loadResults();
                        } else if (progress.status === 'error') {
                            clearInterval(interval);
                            alert('生成錯誤: ' + progress.message);
                            document.getElementById('progressContainer').style.display = 'none';
                        }
                    }
                } catch (error) {
                    clearInterval(interval);
                    alert('進度查詢失敗: ' + error.message);
                }
            }, 1000);
        }
        
        async function loadResults() {
            try {
                // 載入文件列表
                const documentsResponse = await fetch(`/documents/${currentTaskId}`);
                const documentsData = await documentsResponse.json();
                
                if (documentsResponse.ok) {
                    displayDocuments(documentsData.documents);
                }
                
                document.getElementById('downloadBtn').disabled = false;
                
            } catch (error) {
                alert('載入結果失敗: ' + error.message);
            }
        }
        
        function displayDocuments(documents) {
            const previewArea = document.getElementById('previewArea');
            const documentList = document.getElementById('documentList');
            
            previewArea.style.display = 'block';
            documentList.innerHTML = '';
            
            // 更新統計
            document.getElementById('statsContainer').style.display = 'grid';
            document.getElementById('totalCount').textContent = documents.length;
            document.getElementById('aiGenerated').textContent = documents.length;
            
            documents.forEach((document, index) => {
                const documentDiv = window.document.createElement('div');
                documentDiv.className = 'document-preview';
                
                const basicInfo = document.basic_info;
                const content = document.content;
                const traits = document.personality_traits;
                const docType = document.document_type;
                
                const traitsHTML = Object.entries(traits).map(([key, value]) => 
                    `${key}: ${value}`
                ).join(' | ');
                
                documentDiv.innerHTML = `
                    <div class="document-header">
                        <h2>${basicInfo.name} ${docType === 'job_application' ? '(求職履歷)' : '(學習歷程)'}</h2>
                        <p><strong>聯絡資訊：</strong>${basicInfo.email} | ${basicInfo.phone} | ${basicInfo.city} | ${basicInfo.age}歲</p>
                        <p><strong>個人特質：</strong>${traitsHTML}</p>
                    </div>
                    
                    ${Object.entries(content).map(([key, value]) => {
                        const sectionTitles = {
                            'education': '🎓 學歷背景/學業表現',
                            'language_skills': '🌍 語言能力',
                            'experience': '💼 工作經驗/課外活動',
                            'technical_skills': '🛠️ 專業技能/競賽經驗',
                            'certificates': '🏆 證照資格/志工服務',
                            'projects': '🚀 專案經驗/專題研究',
                            'personality': '👤 個人特質描述',
                            'vision': '🎯 願景/學習動機'
                        };
                        
                        return `
                            <div class="document-section">
                                <h3>${sectionTitles[key] || key}</h3>
                                <p>${value.replace(/\\n/g, '<br>')}</p>
                            </div>
                        `;
                    }).join('')}
                    
                    <button class="btn" onclick="downloadSinglePDF(${index})">下載此文件PDF</button>
                `;
                
                documentList.appendChild(documentDiv);
            });
        }
        
        function downloadSinglePDF(index) {
            if (!currentTaskId) {
                alert('請先生成文件');
                return;
            }
            
            window.open(`/download/${currentTaskId}/${index}`, '_blank');
        }
        
        function downloadAllPDFs() {
            if (!currentTaskId) {
                alert('請先生成文件');
                return;
            }
            
            window.open(`/download_all/${currentTaskId}`, '_blank');
        }
        
        function clearResults() {
            currentTaskId = null;
            document.getElementById('previewArea').style.display = 'none';
            document.getElementById('statsContainer').style.display = 'none';
            document.getElementById('progressContainer').style.display = 'none';
            document.getElementById('downloadBtn').disabled = true;
            document.getElementById('documentList').innerHTML = '';
        }
    </script>
</body>
</html>'''
    
    # 寫入HTML模板
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print("🤖 AI履歷生成器啟動中...")
    print("📁 請安裝依賴: pip install flask reportlab google-generativeai")
    print("🔑 請設定 GEMINI_API_KEY 環境變數以啟用AI生成功能")
    print("🌐 網站將在 http://127.0.0.1:5000 啟動")
    
    app.run(debug=True, host='127.0.0.1', port=5000)