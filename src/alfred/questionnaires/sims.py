# -*- coding:utf-8 -*-

from alfred.question import CompositeQuestion
from alfred.element import LikertListElement, TextElement

def sims(aufgabe, language='de', shuffle=False, tag='SIMS', uid=None, title=None, subtitle=None, statustext=None, forceInput = True):
    instruction_intro = {'de': u'Bitte lesen Sie sich jede der folgenden Aussagen sorgfältig durch. Markieren Sie dann bei jeder Aussage, in wie fern sie Ihren tatsächlichen Gründen entspricht, die betreffende Aktivität auszuführen. Orientieren Sie sich dabei an folgender Skala:<br><br>1 - trifft überhaupt nicht zu<br>2 - trifft sehr wenig zu<br>3 - trifft wenig zu<br>4 - trifft mittelmäßig zu<br>5 - trifft hinreichend zu<br>6 - trifft sehr zu<br>7 - trifft exakt zu'}
    instruction = {'de': u"Warum beschäftigen Sie sich gegenwärtig mit %s?" % aufgabe}
    labels = ['1','2','3','4','5','6','7']
    items = {}
    items['de'] = [
            u"Weil ich denke, dass diese Aufgabe interessant ist",
            u"Ich tue es zu meinem eigenen Besten",
            u"Weil ich es tun soll",
            u"Es mag gute Gründe für diese Aufgabe geben, persönlich sehe ich aber keine",
            u"Weil diese Aufgabe angenehm ist",
            u"Weil ich denke, dass diese Aufgabe gut für mich ist",
            u"Weil es etwas ist, dass ich tun muss",
            u"Ich bearbeite diese Aufgabe, aber ich bin nicht sicher, ob sie es wert ist",
            u"Weil diese Aufgabe Spaß macht",
            u"Es ist meine persönliche Entscheidung",
            u"Ich habe keine andere Wahl",
            u"Ich weiß es nicht. Ich sehe nicht, was mir diese Aufgabe bringt",
            u"Weil ich mich bei dieser Aufgabe gut fühle",
            u"Weil ich glaube, dass diese Aufgabe wichtig für mich ist",
            u"Ich habe das Gefühl, es tun zu müssen",
            u"Ich bearbeite diese Aufgabe, aber ich bin mir nicht sicher, ob es eine gute Sache ist, sie fortzuführen",
        ]
    items['en'] = [
            'Because I think that this activity is interesting',
            'Because I think that this activity is pleasant',
            'Because this activity is fun',
            'Because I feel good when doing this activity',
            'Because I am doing it for my own good',
            'Because I think that this activity is good for me',
            'By personal decision',
            'Because I believe that this activity is important for me',
            'Because I am supposed to do it',
            'Because it is something that I have to do',
            'Because I don’t have any choice',
            'Because I feel that I have to do it',
            'There may be good reasons to do this activity, but personally I don’t see any',
            'I do this activity but I am not sure if it is worth it',
            'I don’t know; I don’t see what this activity brings me',
            'I do this activity, but I am not sure it is a good thing to pursue it'
        ]
    
    likert = LikertListElement(instruction[language], levels=7,
            itemLabels=items[language], shuffle=shuffle, topScaleLabels=labels,
            bottomScaleLabels=labels, tableStriped=True, forceInput=forceInput, name='item'    
        )
    
    intro = TextElement(instruction_intro[language])

    q = CompositeQuestion(tag=tag, uid=uid, title=title, subtitle=subtitle, statustext=statustext)
    q.addElements(intro, likert)
    return q

