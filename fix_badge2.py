with open('index.html','r',encoding='utf-8') as f: c=f.read()

# Add CSS for logout button hover
old_style_end = '</style>'
hover_css = '#logout-btn:hover{background:#dc2626!important;color:#fff!important}\n'

# Add before first </style>
if '#logout-btn' not in c:
    c = c.replace('</style>', hover_css + '</style>', 1)
    print('✓ Logout hover CSS added')

with open('index.html','w',encoding='utf-8') as f: f.write(c)
print('Done')
