class ExtZup:
    ext_meta = {
        'name': 'BP_zup',
    }

    def export(self, state):
        state['extensions_used'].append('BP_zup')
