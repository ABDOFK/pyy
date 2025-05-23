from django.contrib import admin
from .models import Conversation, Message

# Enregistrement simple
admin.site.register(Conversation)
admin.site.register(Message)

# ----- Optionnel : Personnalisation -----
# class ConversationAdmin(admin.ModelAdmin):
#     list_display = ('id', 'get_participants_display', 'date_creation', 'date_derniere_activite')
#     filter_horizontal = ('participants',) # Meilleure interface pour ManyToManyField
#     search_fields = ('participants__username',)

#     def get_participants_display(self, obj):
#         return ", ".join([user.username for user in obj.participants.all()])
#     get_participants_display.short_description = 'Participants' # Nom de la colonne

# class MessageAdmin(admin.ModelAdmin):
#     list_display = ('conversation', 'auteur', 'contenu_court', 'timestamp')
#     list_filter = ('timestamp', 'auteur')
#     search_fields = ('contenu', 'auteur__username', 'conversation__id')
#     readonly_fields = ('timestamp',)

#     def contenu_court(self, obj):
#         return obj.contenu[:50] + '...' if len(obj.contenu) > 50 else obj.contenu
#     contenu_court.short_description = 'Contenu (début)'

# admin.site.register(Conversation, ConversationAdmin)
# admin.site.register(Message, MessageAdmin)