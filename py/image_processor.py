from PIL import Image
import os

def ensure_directories():
    """必要なディレクトリが存在することを確認し、なければ作成"""
    # プロジェクトのルートディレクトリを取得
    current_dir = os.path.dirname(os.path.abspath(__file__))  # pyディレクトリ
    project_root = os.path.dirname(current_dir)  # プロジェクトルート
    
    directories = [
        os.path.join(project_root, 'static', 'images', 'quiz_info'),
        os.path.join(project_root, 'static', 'images', 'quiz_info', 'optimized')
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

def optimize_image_16_9(input_path, output_path, target_width=800):
    """16:9アスペクト比を維持しながら画像を最適化"""
    with Image.open(input_path) as img:
        # RGBA画像をRGBに変換
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # 16:9のアスペクト比を計算
        target_height = int(target_width * 9 / 16)
        
        # リサイズ
        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # 最適化して保存
        img.save(output_path, 'JPEG', 
                quality=85,  # 画質設定
                optimize=True)

def process_images(input_dir, output_dir, width=800):
    """ディレクトリ内の全画像を16:9で処理"""
    # 入力ディレクトリが存在しない場合はエラー
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    print(f"Searching for images in: {input_dir}")
    
    # 入力ディレクトリ内のファイルを列挙
    files = os.listdir(input_dir)
    image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not image_files:
        print(f"No image files found in {input_dir}")
        return
    
    print(f"Found {len(image_files)} image files")    
    
    for filename in image_files:
            input_path = os.path.join(input_dir, filename)
            output_filename = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, f"optimized_{output_filename}.jpg")
            
            try:
                print(f"Processing {filename}...")
                optimize_image_16_9(input_path, output_path, target_width=width)
                print(f"Successfully processed: {filename} -> {output_path}")
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

if __name__ == "__main__":
    # プログラム実行時にまずディレクトリの存在を確認
    ensure_directories()
    
    # プロジェクトのルートディレクトリからの相対パスを設定
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)    
        
    # 絶対パスで指定
    input_dir = os.path.join(project_root, "static", "images", "quiz_info")
    output_dir = os.path.join(project_root, "static", "images", "quiz_info", "optimized")
    
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    process_images(input_dir, output_dir, width=800)