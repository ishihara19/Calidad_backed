document.addEventListener('DOMContentLoaded', function () {
    function validarPorcentajeTotal() {
        let total = 0;
        // Selecciona todos los inputs de porcentaje asignado dentro del inline
        document.querySelectorAll('input[name$="porcentaje_asignado"]').forEach(function(input){
            let val = parseFloat(input.value);
            if (!isNaN(val)) {
                total += val;
            }
        });
        
        const mensajeId = 'mensaje-porcentaje-total';
        let mensaje = document.getElementById(mensajeId);
        if (!mensaje) {
            mensaje = document.createElement('div');
            mensaje.id = mensajeId;
            mensaje.style.fontWeight = 'bold';
            mensaje.style.margin = '10px 0';
            document.querySelector('.inline-group').prepend(mensaje);
        }
        
        if (total > 100) {
            mensaje.style.color = 'red';
            mensaje.textContent = `⚠️ La suma del porcentaje asignado es ${total.toFixed(2)}%. ¡No puede superar 100%!`;
        } else if (total < 100) {
            mensaje.style.color = 'orange';
            mensaje.textContent = `⚠️ La suma del porcentaje asignado es ${total.toFixed(2)}%. Falta completar el 100%.`;
        } else {
            mensaje.style.color = 'green';
            mensaje.textContent = `✅ La suma del porcentaje asignado es 100%. ¡Perfecto!`;
        }
    }
    
    // Validar inicialmente
    validarPorcentajeTotal();
    
    // Validar cada vez que cambia un input
    document.querySelectorAll('input[name$="porcentaje_asignado"]').forEach(function(input){
        input.addEventListener('input', validarPorcentajeTotal);
    });
});
