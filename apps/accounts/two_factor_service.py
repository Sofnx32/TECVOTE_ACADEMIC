import pyotp
import qrcode
import io
import base64
import secrets
import logging

logger = logging.getLogger(__name__)


class TwoFactorService:
    
    @staticmethod
    def generate_secret():
        return pyotp.random_base32()
    
    @staticmethod
    def get_provisioning_uri(secret, email, issuer="TECVOTE"):
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=email, issuer_name=issuer)
    
    @staticmethod
    def generate_qr_code(uri):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    @staticmethod
    def verify_code(secret, code):
        try:
            if not secret or not code:
                return False
                
            clean_code = str(code).strip().replace(" ", "")
            
            # Si el código se transformó en número en el camino y perdió ceros a la izquierda (ej: "4532" -> "004532")
            if len(clean_code) < 6:
                clean_code = clean_code.zfill(6)
                
            totp = pyotp.TOTP(secret)
            
            # Ejecutamos la verificación con la ventana de gracia que ya tenías
            return totp.verify(clean_code, valid_window=2)
        except Exception as e:
            logger.error(f"Error verificado TOTP: {str(e)}")
            return False
    
    @staticmethod
    def generate_backup_codes(count=10):
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        return codes
    
    @staticmethod
    def verify_backup_code(user, code):
        backup_codes = user.two_factor_backup_codes or []
        normalized_code = code.replace("-", "").upper()
        
        for backup_code in backup_codes:
            if backup_code.replace("-", "").upper() == normalized_code:
                backup_codes.remove(backup_code)
                user.two_factor_backup_codes = backup_codes
                user.save(update_fields=['two_factor_backup_codes'])
                return True
        
        return False