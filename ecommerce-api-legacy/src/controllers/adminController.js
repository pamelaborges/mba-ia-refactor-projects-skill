const financialReportService = require('../services/financialReportService');

async function financialReport(req, res) {
    try {
        const report = await financialReportService.buildReport();
        return res.json(report);
    } catch (err) {
        console.error('Erro ao gerar relatório financeiro:', err);
        return res.status(500).send('Erro DB');
    }
}

module.exports = { financialReport };
