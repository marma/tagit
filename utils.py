

def tag_content(content, tags):
    offset = 0

    for t in tags:
        #start_tag = f'<span class="{t.type.name}">'
        #end_tag = '</span>'
        #start_tag = f'<div class="ui left labeled button"><a class="ui basic label">'
        #end_tag = f'</a><div class="ui icon button">{t.type.name}</div></div>'
        start_tag = f'<div class="ui label" style="background: {t.type.color}7f">'
        end_tag = f'<a class="detail">{t.type.name}</a><i class="delete icon"></i></div>'    

        content = content[:t.start + offset] + \
                  start_tag + \
                  content[t.start + offset:t.stop + offset] + \
                  end_tag + \
                  content[t.stop + offset:]

        offset += len(start_tag) + len(end_tag)

    return content

