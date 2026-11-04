import subprocess, sys, os, tempfile

repo = r'C:\Users\gabim\Documents\Desafio Técnico - AI Engineer'
hashes = ['4925b70','0172999','c29b0b0','24d76df','a48de51','ee381fd','5ce31b2','73573ab','8e4228f']
python_exe = sys.executable

for h in hashes:
    # get file content
    try:
        content = subprocess.check_output(['git','show',f'{h}:ui/app.py'], cwd=repo, text=True)
    except subprocess.CalledProcessError as e:
        print(f'{h} | missing | False | False | False | False')
        continue
    # write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(content)
        temp_path = f.name
    # compile
    compile_ok = True
    try:
        subprocess.check_output([python_exe, '-m', 'py_compile', temp_path], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        compile_ok = False
    # search features
    txt = content
    has_sidebar = 'st.sidebar' in txt
    has_rerun = 'st.rerun' in txt
    has_selector = ('st.sidebar.radio' in txt) or ('st.sidebar.selectbox' in txt)
    has_list = ('for i, file_path' in txt) or ('saved_chats' in txt) or ('saved_files' in txt)
    print(f'{h} | {compile_ok} | {has_sidebar} | {has_rerun} | {has_selector} | {has_list}')
    os.remove(temp_path)