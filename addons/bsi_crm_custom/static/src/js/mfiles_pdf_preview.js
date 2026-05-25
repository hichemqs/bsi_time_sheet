/** @odoo-module */

import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

const { useEffect } = owl;

export class PdfPreviewDialog extends Dialog {
    setup() {
        super.setup();
        useEffect((modalEl) => {
            if (modalEl) {
                const modalBody = modalEl.querySelector('.modal-body');
                const iframe = document.createElement("iframe");
                
                // Convert base64 to blob URL
                const binaryData = this.props.binaryData;
                const blob = this.base64ToBlob(binaryData, 'application/pdf');
                const blobUrl = URL.createObjectURL(blob);
                
                iframe.src = "/web/static/lib/pdfjs/web/viewer.html?file=" + encodeURIComponent(blobUrl);
                iframe.style.width = "100%";
                iframe.style.minHeight = "550px";
                modalBody.append(iframe);
            }
        }, () => [document.querySelector(':not(.o_inactive_modal).o_dialog')]);
    }

    base64ToBlob(base64, contentType) {
        const byteCharacters = atob(base64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        return new Blob([new Uint8Array(byteNumbers)], { type: contentType });
    }
}

PdfPreviewDialog.props = {
    ...Dialog.props,
    binaryData: { type: String },
    close: Function,
};
delete PdfPreviewDialog.props.slots;

const clientActions = registry.category("actions");

clientActions.add("preview_binary_pdf", (env, action) => {
    const binaryData = action.context && action.context.binary_data;
    
    env.services.dialog.add(PdfPreviewDialog, {
        binaryData: binaryData,
        title: _t('Aperçu PDF'),
        size: 'xl',
        withBodyPadding: false,
    });
});
