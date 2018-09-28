# -*- coding:utf-8 -*-

from alfred.question import CompositeQuestion
from alfred.element import LikertListElement

def ray(language='de', shuffle=False, tag='RAY', uid=None, title=None, subtitle=None, statustext=None, forceInput=True):
    labels = {'de': ['Ja', 'keine Angabe', 'Nein']}
    instruction = {'de': u'Bitte geben Sie an, in wie fern die folgenden Aussagen auf Sie zutreffen (Ja/keine Angabe/Nein):'}
    items = {}
    items['de'] = [
            u"Ist es Ihnen wichtiger einer angenehmen Tätigkeit nachzugehen als Karriere zu machen?",
            u"Sind sie damit zufrieden in Ihrer Tätigkeit / Ihrem Beruf nicht besser zu sein als die meisten anderen Leute?",
            u"Gefällt es Ihnen die Arbeitsweise der Organisation zu verbessern, der sie angehören?",
            u"Machen Sie sich die Mühe Kontakte zu Menschen zu pflegen, die Ihnen bei Ihrer Karriere nützlich sein können?",
            u"Sind Sie ruhelos und genervt, wenn Sie das Gefühl haben Zeit zu verschwenden?",
            u"Haben Sie immer hart gearbeitet, um zu den Besten Ihrer Branche (Schule, Organisation, Beruf) zu gehören?",
            u"Würden Sie es eher vorziehen mit einem angenehmen aber inkompetenten Partner zu arbeiten, als mit einem schwierigen aber hochkompetenten Partner?",
            u"Neigen Sie dazu, für Ihren Beruf oder Ihre Karriere im Voraus zu planen?",
            u"Ist es Ihnen wichtig „im Leben weiterzukommen“?",
            u"Sind Sie eine ehrgeizige Person?",
            u"Möchten Sie lieber von den Erfolgen Anderer lesen, als sich die Arbeit zu machen selbst erfolgreich zu sein?",
            u"Würden Sie sich selbst als faul beschreiben?",
            u"Vergehen oft Tage, ohne dass Sie etwas gemacht haben?",
            u"Nehmen Sie das Leben wie es kommt, ohne viel Planung?",
        ]



    e = LikertListElement(instruction = instruction[language], levels=3,
            itemLabels=items[language], shuffle=shuffle, topScaleLabels=labels[language], itemLabelWidth = 600,
            bottomScaleLabels=labels[language], tableStriped=True, forceInput=forceInput, name='item'
        )

    q = CompositeQuestion(tag=tag, uid=uid, title=title, subtitle=subtitle, statustext=statustext)
    q.addElement(e)
    return q
