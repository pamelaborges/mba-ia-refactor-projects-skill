const userRepository = require('../repositories/userRepository');

async function deleteUser(req, res) {
    const { id } = req.params;

    try {
        const changes = await userRepository.remove(id);
        if (changes === 0) {
            return res.status(404).json({ error: 'Usuário não encontrado' });
        }
        return res.json({ message: 'Usuário deletado com sucesso' });
    } catch (err) {
        if (err.code === 'SQLITE_CONSTRAINT') {
            return res.status(409).json({
                error: 'Não é possível deletar usuário com matrículas ou pagamentos associados',
            });
        }
        console.error('Erro ao deletar usuário:', err);
        return res.status(500).json({ error: 'Erro ao deletar usuário' });
    }
}

module.exports = { deleteUser };
