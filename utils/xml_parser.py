def get_branch(tree,regulations):
    for branch in tree: 
        if branch.tag!= 'DIV8':
            get_branch(branch,regulations)
        else:
            title_found = False
            for index, text in enumerate(branch.itertext()):
                if not title_found and text.strip(' ') =='\n':
         
                    next
                if not title_found and text.strip(' ')!= '\n':
                    regulations.append({
                        'title': text,
                        'content': ''
                    })
                    title_found = True
                    continue
                if title_found:
                    regulations[-1]['content']+=text.strip()