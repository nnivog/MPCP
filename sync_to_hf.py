import os
from huggingface_hub import HfApi

token = os.environ.get('HF_TOKEN', '')
if not token:
    raise ValueError('HF_TOKEN is empty! Check GitHub Secrets.')

print(f'Token found: {token[:6]}...')

HfApi().upload_folder(
    folder_path='.',
    repo_id='Govinn/MPCP',
    repo_type='space',
    token=token,
    ignore_patterns=[
        '*.bak',
        '.git*',
        '__pycache__',
        '*.pyc',
        'patch_*.py',
        'fix_*.py',
        'sync_to_hf.py',
        '*.rar',
        '*.zip'
    ]
)
print('Synced to HF Space: Govinn/MPCP')
